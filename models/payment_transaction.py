
import logging
import pprint

from werkzeug import urls

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.payment_wompi.controllers.main import WompiController

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'


    def _get_specific_rendering_values(self, processing_values):
        """ Override of payment to return Wompi-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of provider-specific processing values
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'wompi':
            return res

        amount_in_cents = int(self.amount * 100)
        currency = self.currency_id.name
        reference = self.reference
        base_url = self.provider_id.get_base_url()
        str_to_sign = f'{reference}{amount_in_cents}{currency}{self.provider_id.wompi_integrity_secret}'
        signature = self.provider_id._wompi_generate_signature(str_to_sign)

        if isinstance(reference, str):
            reference = reference.encode('utf-8')

        if isinstance(currency, str):
            currency = currency.encode('utf-8')     

        return {
            'public_key': self.provider_id.wompi_public_key,
            'amount_in_cents': amount_in_cents,
            'currency': currency.decode('utf-8') if isinstance(currency, bytes) else currency,
            'reference': reference.decode('utf-8') if isinstance(reference, bytes) else reference,
            'redirect_url': urls.url_join(base_url, WompiController._return_url),
            'signature_integrity': signature,
            'api_url': self.provider_id._wompi_get_checkout_url()
        
        }

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """ Override of payment to find the transaction based on Wompi data.

        :param str provider_code: The code of the provider that handled the transaction
        :param dict notification_data: The notification data sent by the provider
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if the data match no transaction
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'wompi' or len(tx) == 1:
            return tx
        data = notification_data.get('data', {})
        if not data:
            raise ValidationError("Wompi: " + _("Received data with missing data."))

        reference = data.get('reference') or data.get('transaction').get('reference')
        if not reference:
            raise ValidationError("Wompi: " + _("Received data with missing reference."))

        tx = self.search([('reference', '=', reference)])
        if not tx:
            raise ValidationError(
                "Wompi: " + _("No transaction found matching reference %s.", reference)
            )
        return tx
    
    def _process_notification_data(self, notification_data):
        """ Override of payment to process the transaction based on Wompi data.

        Note: self.ensure_one() from `_process_notification_data`

        :param dict notification_data: The notification data sent by the provider
        :return: None
        :raise: ValidationError if inconsistent data were received
        """
        super()._process_notification_data(notification_data)
        if self.provider_code != 'wompi':
            return
        _logger.info("_process_notification_data:\n%s", pprint.pformat(notification_data))
        data = notification_data.get('data', {})
        if not data:
            raise ValidationError("Wompi: " + _("Received data with missing data."))
        transaction_id = data.get('id') or data.get('transaction').get('id')
        amount_in_cents = data.get('amount_in_cents') or data.get('transaction').get('amount_in_cents')  
        status = data.get('status') or data.get('transaction').get('status')
        timestamp = notification_data.get('timestamp')

        if 'signature' in notification_data:
            signature = notification_data.get('signature').get('checksum')
        else:
            signature = None

        if timestamp and signature:
            str_to_sign = f"{transaction_id}{status}{amount_in_cents}{timestamp}{self.provider_id.wompi_events_key}"
            if self.provider_id._wompi_generate_signature(str_to_sign) != signature:
                raise ValidationError("Wompi: " + _("Received data with invalid signature."))

        if status == 'APPROVED':
            self._set_done()
        elif status == 'DECLINED' or status == 'ERROR' or status == 'VOIDED':
            self._set_canceled()
        else:
            raise ValidationError(
                "Wompi: " + _("Received data with unknown status %s.", status)
            )
