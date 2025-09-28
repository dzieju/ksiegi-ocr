# Updated gui/mail_config_widget.py

import logging

# Configure logging to output to console
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Existing code ...

# New authentication method list
AUTHENTICATION_METHODS = ['PLAIN', 'LOGIN', 'XOAUTH2']

logger.debug("Debug logging is enabled.")
logger.debug("Available authentication methods: %s", AUTHENTICATION_METHODS)

# Existing code ...
