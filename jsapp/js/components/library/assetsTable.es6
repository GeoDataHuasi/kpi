import React from 'react';
import autoBind from 'react-autobind';
import {bem} from 'js/bem';
import {t} from 'js/utils';
import AssetsTableRow from './assetsTableRow';
import {renderLoading} from 'js/components/modalForms/modalHelpers';

export const ASSETS_TABLE_CONTEXTS = new Map();
new Set([
  'my-library',
  'collection-content',
  'public-collections'
]).forEach((name) => {ASSETS_TABLE_CONTEXTS.set(name, name);});

/**
 * @typedef AssetsTableColumn
 * @prop {string} label
 * @prop {string} id
 * @prop {string} backendProp - path to property data (for ordering)
 * @prop {boolean} defaultIsOrderAsc
 */
export const ASSETS_TABLE_COLUMNS = new Map([
  [
    'country', {
      label: t('Country'),
      id: 'country',
      backendProp: 'settings.country',
      defaultIsOrderAsc: true
    }
  ],
  [
    'icon-status', {
      label: null,
      id: 'icon-status',
      backendProp: 'asset_type',
      defaultIsOrderAsc: true
    }
  ],
  [
    'languages', {
      label: t('Languages'),
      id: 'languages',
      backendProp: 'settings.languages',
      defaultIsOrderAsc: true
    }
  ],
  [
    'last-modified', {
      label: t('Last Modified'),
      id: 'last-modified',
      backendProp: 'date_modified',
      defaultIsOrderAsc: false
    }
  ],
  [
    'name', {
      label: t('Name'),
      id: 'name',
      backendProp: 'name',
      defaultIsOrderAsc: true
    }
  ],
  [
    'organization', {
      label: t('Organization'),
      id: 'organization',
      backendProp: 'settings.organization',
      defaultIsOrderAsc: true
    }
  ],
  [
    'owner', {
      label: t('Owner'),
      id: 'owner',
      backendProp: 'owner__username',
      defaultIsOrderAsc: true
    }
  ],
  [
    'primary-sector', {
      label: t('Primary Sector'),
      id: 'primary-sector',
      backendProp: 'settings.sector',
      defaultIsOrderAsc: true
    }
  ],
  [
    'subscribers', {
      label: t('Subscribers'),
      id: 'subscribers',
      backendProp: 'subscribers_count',
      defaultIsOrderAsc: true
    }
  ]
]);

/**
 * @callback reorderCallback
 * @param {AssetsTableColumn} orderBy
 * @param {boolean} isOrderAsc
 */

/**
 * @callback switchPageCallback
 * @param {string} pageNumber
 */

/**
 * Displays a table of assets.
 *
 * @prop {string} context - One of ASSETS_TABLE_CONTEXTS.
 * @prop {Array<object>} assets - List of assets to be displayed.
 * @prop {string} [emptyMessage] - To replace the default empty message.
 * @prop {boolean} [isLoading] - To display spinner.
 * @prop {AssetsTableColumn} orderBy - Current order column, one of ASSETS_TABLE_COLUMNS.
 * @prop {boolean} isOrderAsc - Current order direction.
 * @prop {reorderCallback} onReorder - Called when user clicks column header for reordering.
 * @prop {number} [currentPage] - For displaying pagination.
 * @prop {number} [totalPages] - For displaying pagination.
 * @prop {switchPageCallback} [onSwitchPage] - Called when user clicks page change.
 */
export class AssetsTable extends React.Component {
  constructor(props){
    super(props);
    autoBind(this);
  }

  /**
   * This function is only a callback handler, as the asset reordering itself
   * should be handled by the component that is providing the assets list.
   * @param {string} columnId
   */
  reorder(columnId) {
    if (this.props.orderBy.id === columnId) {
      // clicking already selected column results in switching the order direction
      this.props.onReorder(this.props.orderBy, !this.props.isOrderAsc);
    } else {
      // change column and revert order direction to ascending
      const newColumn = ASSETS_TABLE_COLUMNS.get(columnId);
      this.props.onReorder(newColumn, newColumn.defaultIsOrderAsc);
    }
  }

  renderHeaderColumn(columnDef) {
    // empty icon to take up space in column
    let icon = (<i className='k-icon'/>);
    if (this.props.orderBy.id === columnDef.id) {
      if (this.props.isOrderAsc) {
        icon = (<i className='k-icon k-icon-up'/>);
      } else {
        icon = (<i className='k-icon k-icon-down'/>);
      }
    }
    return (
      <bem.AssetsTableRow__column
        m={columnDef.id}
        onClick={this.reorder.bind(this, columnDef.id)}
      >
        {columnDef.label}
        {icon}
      </bem.AssetsTableRow__column>
    );
  }

  renderFooter() {
    // TODO pagination!

    return (
      <bem.AssetsTable__footer>
        <span>
          {t('##count## items available').replace('##count##', this.props.assets.length)}
        </span>

        <span>
          {this.props.currentPage + 1} / {this.props.totalPages}
        </span>
      </bem.AssetsTable__footer>
    );
  }

  render() {
    return (
      <bem.AssetsTable m={this.props.context}>
        <bem.AssetsTable__header>
          <bem.AssetsTableRow m='header'>
            {this.renderHeaderColumn(ASSETS_TABLE_COLUMNS.get('icon-status'))}
            {this.renderHeaderColumn(ASSETS_TABLE_COLUMNS.get('name'))}
            {this.renderHeaderColumn(ASSETS_TABLE_COLUMNS.get('owner'))}
            {this.props.context === ASSETS_TABLE_CONTEXTS.get('public-collections') &&
              this.renderHeaderColumn(ASSETS_TABLE_COLUMNS.get('subscribers'))
            }
            {this.renderHeaderColumn(ASSETS_TABLE_COLUMNS.get('organization'))}
            {this.renderHeaderColumn(ASSETS_TABLE_COLUMNS.get('languages'))}
            {this.renderHeaderColumn(ASSETS_TABLE_COLUMNS.get('primary-sector'))}
            {this.renderHeaderColumn(ASSETS_TABLE_COLUMNS.get('country'))}
            {this.renderHeaderColumn(ASSETS_TABLE_COLUMNS.get('last-modified'))}
          </bem.AssetsTableRow>
        </bem.AssetsTable__header>

        <bem.AssetsTable__body>
          {this.props.isLoading &&
            renderLoading()
          }

          {!this.props.isLoading && this.props.assets.length === 0 &&
            <bem.AssetsTableRow m='empty-message'>
              {this.props.emptyMessage || t('There are no assets to display.')}
            </bem.AssetsTableRow>
          }

          {!this.props.isLoading && this.props.assets.map((asset) => {
            return (
              <AssetsTableRow
                asset={asset}
                key={asset.uid}
                context={this.props.context}
              />
            );
          })}
        </bem.AssetsTable__body>

        {this.renderFooter()}
      </bem.AssetsTable>
    );
  }
}
