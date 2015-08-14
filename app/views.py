from django.http import HttpResponse, HttpResponseForbidden
from app.models import SocialNetwork
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


def fb_real_time_updates(request):
    logger.info('Got a request!')
    if request.method == 'GET':
        challenge = request.GET.get('hub.challenge')
        token = request.GET.get('hub.verify_token')
        fb = SocialNetwork.objects.get(name__contains='facebook')
        if fb.token_real_time_updates == token:
            logger.info('Token received!')
            return HttpResponse(challenge)
        else:
            logger.warning('Token is not the same!')
            return HttpResponseForbidden()
    elif request.method == 'POST':
        logger.info('There is an update!')
        return HttpResponse()
    else:
        return HttpResponseForbidden()
