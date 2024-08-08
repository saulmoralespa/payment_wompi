
import logging
import hashlib

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.payment_wompi.const import SUPPORTED_CURRENCIES


_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('wompi', "Wompi")], ondelete={'wompi': 'set default'}
    )
    wompi_public_key = fields.Char(
        string="Public Key",
        help="Public key provided by Wompi",
        required_if_provider='wompi')
    wompi_events_key = fields.Char(
        string="Events Key",
        help="Public events provided by Wompi",
        required_if_provider='wompi')
    wompi_integrity_secret = fields.Char(
        string="Integrity Secret",
        help="Integrity Secret provided by Wompi",
        required_if_provider='wompi')

    #=== COMPUTE METHODS ===#

    def _compute_feature_support_fields(self):
        """ Override of `payment` to enable additional features. """
        super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == 'wompi').update({
            'support_fees': True,
        })

    # === BUSINESS METHODS ===#

    @api.model
    def _get_compatible_providers(self, *args, currency_id=None, **kwargs):
        """ Override of payment to unlist Wompi providers when the currency is not supported. """
        providers = super()._get_compatible_providers(*args, currency_id=currency_id, **kwargs)

        currency = self.env['res.currency'].browse(currency_id).exists()
        if currency and currency.name not in SUPPORTED_CURRENCIES:
            providers = providers.filtered(lambda p: p.code != 'wompi')

        return providers


    def _wompi_get_checkout_url(self):
        """ Return the API URL according to the provider state.

        Note: self.ensure_one()

        :return: The API URL
        :rtype: str
        """
        self.ensure_one()

        return 'https://checkout.wompi.co/p/'    
    
    def _wompi_get_api_url(self):
        """ Return the API URL according to the provider state.

        Note: self.ensure_one()

        :return: The API URL
        :rtype: str
        """
        self.ensure_one()

        if self.state == 'enabled':
            return 'https://production.wompi.co/v1'
        else:
            return 'https://sandbox.wompi.co/v1'


    def _wompi_generate_signature(self, string):
        """ Generate the signature integrity for the transaction.

        Note: self.ensure_one()

        :param float amount: The amount of the transaction
        :param str currency: The currency of the transaction
        :param str reference: The reference of the transaction
        :return: The signature integrity
        :rtype: str
        """
        self.ensure_one()
        
        string_bytes = string.encode('utf-8')
        m = hashlib.sha256()
        m.update(string_bytes)
        signature = m.hexdigest()

        return signature
