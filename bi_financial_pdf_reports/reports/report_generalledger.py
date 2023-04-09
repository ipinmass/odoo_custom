# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


from odoo import api, models

class GeneralLedgerReport(models.AbstractModel):
    _name = 'report.bi_financial_pdf_reports.report_generalledger'
    _description = 'General Ledger Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        return {
            'doc_ids': docids,
            'doc_model': 'accounting.report.bi',
            'data': data,
        }
