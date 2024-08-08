-- disable wompi payment provider
UPDATE payment_provider
   SET wompi_public_key = NULL,
       wompi_events_key = NULL,
       wompi_integrity_secret = NULL;