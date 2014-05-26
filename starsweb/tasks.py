from django.core.files.base import ContentFile

from celery.utils.log import get_task_logger
from celery import shared_task

from . import models

import tempfile
import shutil

logger = get_task_logger(__name__)


@shared_task
def activate_game(pk):
    try:
        game = models.Game.objects.get(pk=pk)

        logger.info(
            "Beginning game activation on '{game.name}'"
            " (pk={game.pk}).".format(game=game)
        )

        # Create a temporary directory for Stars to work in.
        temp = tempfile.mkdtemp()

        logger.info("Created temp directory for '{game.name}' (pk={game.pk}):"
                    " {temp}".format(game=game, temp=temp))

        # Activate.
        game.activate(temp)

        # Delete the temp directory.
        shutil.rmtree(temp)

        logger.info(
            "Finishing game creation on '{game.name}' (pk={game.pk}).".format(
                game=game)
        )
    except Exception as e:
        logger.exception(
            "Game creation failed on '{game.name}' (pk={game.pk})".format(
                game=game)
        )
        raise activate_game.retry(exc=e)


@shared_task
def generate(pk):
    try:
        game = models.Game.objects.get(pk=pk)

        logger.info(
            "Beginning turn generation on '{game.name}'"
            " (pk={game.pk}).".format(game=game)
        )

        # Create a temporary directory for Stars to work in.
        temp = tempfile.mkdtemp()

        logger.info("Created temp directory for '{game.name}' (pk={game.pk}):"
                    " {temp}".format(game=game, temp=temp))

        # Generate.
        game.generate(temp)

        # Delete the temp directory.
        shutil.rmtree(temp)

        logger.info(
            "Finishing turn generation on '{game.name}'"
            " (pk={game.pk}).".format(game=game)
        )
    except Exception as e:
        logger.exception(
            "Turn generation failed on '{game.name}' (pk={game.pk})".format(
                game=game)
        )
        raise generate.retry(exc=e)
