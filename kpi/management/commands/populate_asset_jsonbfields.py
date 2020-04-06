# coding: utf-8
from django.core.management.base import BaseCommand

from kpi.fields import KpiUidField
from django.contrib.postgres.fields import JSONField as JSONBField

from kpi.models.asset import Asset

from django.db import models
from django.core.paginator import Paginator

import sys
import json

UPDATE_BATCH_COUNT = 1000
DOTS_EVERY = 20

#  >  python manage.py populate_asset_jsonbfields
# will iterate through the kpi.asset table and copy all values of asset.content
# over to asset.content_jsonb

INFO = '''
Backfilling jsonb fields of "kpi.Asset" for {} records.
* content => content_jsonb
* _deployment_data => _deployment_data_jsonb
* summary => summary_jsonb

Each dot represents {} assets being backfilled.
'''

TEXT_FIELDS = ['content', 'summary', '_deployment_data']
JSONB_FIELDS = ['content_jsonb', 'summary_jsonb', '_deployment_data_jsonb']


def _backfill(asset_query):
    '''
    This method is called on a query of the 'kpi.asset'

    The purpose is to copy all json text fields to jsonb until the table is
    ready to switch over to jsonb and drop the text fields.

    The table is corrected in batches, ordered by date_created (newest first)

    We want to copy fields when x_jsonb field is empty and x is not empty.
    I.e. when these criteria are met
    * content          is in [None, '{}'] AND content_jsonb is in [None, {}]
    * _deployment_data ''
    * summary          ''
    '''
    asset = Asset(id=asset_query.pop('id'),
                  uid=asset_query.pop('uid'),
                  )

    has_change = False
    for field in TEXT_FIELDS:
        text = asset_query[field]
        jsonb = asset_query[field + '_jsonb']
        if text not in [None, '{}'] and jsonb in [None, {}]:
            has_change = True
    if not has_change:
        return None
    for field in TEXT_FIELDS:
        text = asset_query[field]
        val = {}
        if text is not None:
            val = json.loads(text.replace('\\u0000', ''))
        setattr(asset, field + '_jsonb', val)
    return asset

def populate_asset_jsonbfields():
    print(INFO.format(
        Asset.objects.count(),
        DOTS_EVERY,
    ))

    query_fields = TEXT_FIELDS + JSONB_FIELDS + ['id', 'uid', 'date_created']
    asset_qs = Asset.objects.order_by('-date_created').values(*query_fields)
    paginator = Paginator(asset_qs, UPDATE_BATCH_COUNT)

    total_seen = 0
    for page in range(1, paginator.num_pages + 1):
        total_changed = 0
        arr = []
        for asset_query in paginator.page(page).object_list:
            total_seen += 1
            latest_record_date = asset_query['date_created']
            asset = _backfill(asset_query)
            if asset:
                total_changed += 1
                arr.append(asset)
            if total_seen % DOTS_EVERY == 0:
                sys.stdout.write('.')
                sys.stdout.flush()
        if len(arr) > 0:
            Asset.objects.bulk_update(arr, JSONB_FIELDS)
        infostring = '\n' + ' '.join([
            'batch {} out of {} complete'.format(page, paginator.num_pages),
            '(batch size {})'.format(UPDATE_BATCH_COUNT),
            'up to {}'.format(latest_record_date.strftime('%D')),
            '# changed: {}'.format(total_changed),
        ])
        print(infostring)

#  >  python manage.py populate_asset_jsonbfields --check=10
# will run through the first 10, last 10, and a random 10 assets
# and throw an error if jsonb fields do not match json text fields

def check_queryset_fields_match(asset_qs, max_n, note=''):
    query_fields = TEXT_FIELDS + JSONB_FIELDS + ['id', 'uid', 'date_created']
    asset_qs_vals = asset_qs.values(*query_fields)
    for asset in asset_qs_vals[0:max_n]:
        test_fields_match(asset, note)


def test_fields_match(asset, note):
    sys.stdout.write(note[0])
    sys.stdout.flush()
    for field in TEXT_FIELDS:
        field2 = '{}_jsonb'.format(field)
        if asset[field] is None:
            asset[field] = '{}'
        v1 = _deterministic_json_dump(json.loads(asset[field]))
        v2 = _deterministic_json_dump(asset[field2])
        if v1 != v2:
            raise ValueError('Asset(uid={}) jsonb and text fields'
                             ' do not match for {}'.format(
                                asset['uid'],
                                field,
                             ))


def check_fields(check_count):
    asset_count = Asset.objects.count()
    maxn = check_count if (check_count < asset_count) else asset_count
    first_assets = Asset.objects.order_by('date_created')
    last_assets = Asset.objects.order_by('-date_created')
    random_assets = Asset.objects.order_by('uid')
    check_queryset_fields_match(first_assets, maxn, note='first')
    check_queryset_fields_match(last_assets, maxn, note='last')
    check_queryset_fields_match(random_assets, maxn, note='random')
    print('''
    Parsing complete. {} records have been checked and for equality.
    If this number is a significant portion of the dataset then it is now
    safe to continue with kpi migration 0027 which removes asset.content and
    renames the mirrored jsonb fields into their place.
    '''.format(check_count * 3))


def _deterministic_json_dump(obj):
    return json.dumps(obj, sort_keys=True)


class Command(BaseCommand):
    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            '--check',
            default=0,
            type=int,
            help='Check table to see if jsonb fields match text fields',
        )

    def handle(self, *args, **options):
        if options['check'] > 0:
            check_fields(options['check'])
        else:
            populate_asset_jsonbfields()
