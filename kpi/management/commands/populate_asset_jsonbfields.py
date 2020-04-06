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

    # TODO: ensure content_jsonb['schema'] is set to *something*

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


class Command(BaseCommand):
    def handle(self, *args, **options):
        populate_asset_jsonbfields()
