Troubleshooting
===============

MOSFETS turn on and stay on until redeem actually starts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This can be addressed with a patched Uboot, in which case **you will see
the mosfets on for a few seconds until the boot reinitializes** the pin
outputs to low until Redeem can take over.