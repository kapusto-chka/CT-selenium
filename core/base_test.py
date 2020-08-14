"""
This module contains all hooks + some calls for allure reports
Order of execution in Behave see below.

before_all
for feature in all_features:
    before_feature
    for outline in feature.scenarios:
        for scenario in outline.scenarios:
            before_scenario
            for step in scenario.steps:
                before_step
                    step.run()
                after_step
            after_scenario
    after_feature
after_all
"""
from allure_commons.types import AttachmentType
import allure

import logging
import re
import sys

from utilities.config import Config
from utilities.log import Logger


def before_all(context):
    if context.config.userdata:
        Config.BROWSER = context.config.userdata.get('browser', Config.BROWSER).lower()
        Config.REUSE = context.config.userdata.get('reuse', Config.REUSE).lower()

    Logger.configure_logging()
    logger = logging.getLogger(__name__)


def after_all(context):
    pass


def before_feature(context, feature):
    logger = logging.getLogger(__name__)

    context.browser = None


def after_feature(context, feature):
    logger = logging.getLogger(__name__)


def before_scenario(context, scenario):
    Logger.create_test_folder(scenario.name)
    logger = logging.getLogger(__name__)

    if context.browser is None:
        try:
            # use in constructor service_args=['--webdriver-logfile=path_to_log'] to debug deeper...
            context.browser = Config.browser_types[Config.BROWSER]()
            context.browser.set_window_size(1920, 1080)
        except Exception:
            logger.error('Failed to start browser: {}'.format(Config.BROWSER))
            raise

    logger.info('Start of test: {}'.format(scenario.name))


def after_scenario(context, scenario):
    logger = logging.getLogger(__name__)

    if scenario.status == 'failed':
        _screenshot = '{}/{}/__Fail.png'.format(Config.LOG_DIR, scenario.name.replace(' ', '_'))

        try:
            context.browser.save_screenshot(_screenshot)
        except Exception:
            logger.error('Failed to take screenshot to: {}'.format(Config.LOG_DIR))
            raise

        try:
            with open(_screenshot, 'rb') as _file:
                allure.attach(_file.read(), '{} fail'.format(scenario.name), AttachmentType.PNG)
        except Exception:
            logger.error('Failed to attach to report screenshot: {}'.format(_screenshot))
            raise

    if not Config.REUSE:
        try:
            context.browser.quit()
        except Exception:
            logger.error('Failed to close browser: {}'.format(Config.BROWSER))
            raise
        context.browser = None

    logger.info('End of test: {}. Status: {} !!!\n\n\n'.format(scenario.name, scenario.status))


def before_step(context, step):
    logger = logging.getLogger(__name__)


def after_step(context, step):
    logger = logging.getLogger(__name__)

    if step.status.name == 'failed':  # get last traceback and error message
        context.last_traceback = step.error_message
        if step.error_message is not None:
            try:
                context.last_error_message = step.error_message.split('ERROR:')[1]
            except IndexError:
                context.last_error_message = step.error_message
