
import logging
import pprint

import requests
from odoo import _, http
from odoo.exceptions import ValidationError
from odoo.http import request

from odoo.addons.payment.models.payment_provider import PaymentProvider

_logger = logging.getLogger(__name__)


class WompiController(http.Controller):
    _return_url = '/payment/wompi/return/'
    _webhook_url = '/payment/wompi/webhook/'

    @http.route(_return_url, type='http', methods=['GET'], auth='public')
    def wompi_return_from_checkout(self, **data):
        """ Handle the return from the Wompi checkout.

        :param dict data: The data returned from the Wompi checkout
        :return: The response
        """
        # Handle the notification data.
        _logger.info("handling redirection from Wompi with data:\n%s", pprint.pformat(data))
        if not data:  # The customer has canceled or paid then clicked on "Return to Merchant"
            pass  # Redirect them to the status page to browse the (currently) draft transaction
        else:
            try:
                notification_data = self._verify_pdt_notification_origin(data)
            except Forbidden:
                _logger.exception("could not verify the origin of the PDT; discarding it")
            else:
                # Handle the notification data
                request.env['payment.transaction'].sudo()._handle_notification_data('wompi', notification_data)

        # Redirect the user to the status page.
        return request.redirect('/payment/status')

    def _verify_pdt_notification_origin(self, data):
        """ Verify the origin of the PDT notification.

        :param dict data: The data received from the PDT notification
        :return: True if the origin is correct
        :rtype: bool
        """
        if 'id' not in data:  # PDT is not enabled; Wompi directly sent the notification data.
            raise Forbidden("Wompi: PDT are not enabled; cannot verify data origin")
        else:
            PaymentProvider = request.env['payment.provider'].sudo()
            provider = PaymentProvider.search([('code', '=', 'wompi')], limit=1)
            url = provider._wompi_get_api_url() + '/transactions/' + data['id']
            try:
                headers={
                    'Authorization': 'Bearer ' + provider.wompi_public_key,
                    'Accept': 'application/json'
                }
                response = requests.get(url, headers)
                response.raise_for_status()
                notification_data = response.json()
            except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError):
                raise Forbidden("Wompi: Encountered an error when verifying PDT origin")

        return notification_data        


    @http.route(_webhook_url, type='http', auth='public', methods=['POST'], csrf=False)
    def wompi_webhook(self, **_kwargs):
        """ Handle the webhook from Wompi.

        :param dict _kwargs: The extra query parameters.
        :return: The response
        """
        data = request.get_json_data()
        _logger.info("handling webhook from Wompi with data:\n%s", pprint.pformat(data))
        request.env['payment.transaction'].sudo()._handle_notification_data(
            'wompi', data
        )
        return ''  # Acknowledge the notification.



