from __future__ import absolute_import

from app.models import ConsultationPlatform, Initiative, Author, Location, Idea, Comment, Vote, Campaign
from celery import shared_task
from celery.utils.log import get_task_logger
from connectors.admin import do_request, get_json_or_error, get_url_cb, build_request_url
from django.core.cache import cache
from hashlib import md5


logger = get_task_logger(__name__)


def _update_or_create_author(platform, author):
    try:
        author_obj = Author.objects.get(external_id=author['id'], consultation_platform=platform)
    except Author.DoesNotExist:
        if 'email' not in author.keys() or 'name' not in author.keys():
            # Fetch author inform from consultation platform
            connector = platform.connector
            url_cb = get_url_cb(connector, 'get_user_cb')
            url = build_request_url(url_cb.url, url_cb.callback, {'user_id': author['id']})
            resp = do_request(connector, url, url_cb.callback.method)
            author = get_json_or_error(connector.name, url_cb.callback, resp)
        attr_new_author = {'screen_name': author['name'], 'email': author['email'], 'channel': 'consultation_platform',
                           'external_id': author['id'], 'consultation_platform': platform}
        author_obj = Author(**attr_new_author)
        author_obj.save()

    return author_obj


def _get_or_create_location(location):
    attr_new_location = {'latitude': location['latitude'], 'longitude': location['longitude'],
                         'city': location['city'], 'country': location['country']}
    location_obj, location_created = Location.objects.get_or_create(city=location['city'], country=location['country'],
                                                                    defaults=attr_new_location)
    return location_obj


def _update_or_create_content(platform, raw_obj, model, filters, obj_attrs, editable_fields):
    # Handle content author
    obj_attrs.update({'author': _update_or_create_author(platform, raw_obj['user_info'])})
    # Handle content location
    location = raw_obj['location_info']
    if location:
        obj_attrs.update({'location': _get_or_create_location(location)})
    # Handle content creation or update
    content_obj, content_created = model.objects.get_or_create(defaults=obj_attrs, **filters)
    if not content_created:
        content_obj.exist = True
        for editable_field in editable_fields:
            obj_field = getattr(content_obj, editable_field)
            if obj_field != raw_obj[editable_field]:
                content_obj.has_changed = True
                setattr(content_obj, editable_field, raw_obj[editable_field])
    content_obj.save()

    return content_obj


def _get_parent(platform, content_type, content_id):
    if content_type == 'idea':
        try:
            return {'parent': 'idea', 'parent_idea': Idea.objects.get(source_consultation=platform, cp_id=content_id)}
        except Idea.DoesNotExist:
            return None
    else:
        try:
            return {'parent': 'comment', 'parent_comment': Comment.objects.get(source_consultation=platform, cp_id=content_id)}
        except Comment.DoesNotExist:
            return None


def _do_create_update_comment(platform, initiative, comment):
    filters = {'cp_id': comment['id'], 'source': 'consultation_platform'}
    parent_dict = _get_parent(platform, comment['parent_type'], comment['parent_id'])
    if parent_dict:
        if comment['parent_type'] == 'idea':
            campaign = parent_dict['parent_idea'].campaign
        else:
            campaign = parent_dict['parent_comment'].campaign
        comment_attrs = {'cp_id': comment['id'], 'source':'consultation_platform', 'datetime':comment['datetime'],
                         'text': comment['text'], 'url': comment['url'], 'comments': comment['comments'],
                         'initiative': initiative, 'campaign': campaign, 'source_consultation': platform,
                         'positive_votes': comment['positive_votes'], 'negative_votes': comment['negative_votes']}
        comment_attrs.update(parent_dict)
        editable_fields = ('text','comments', 'positive_votes', 'negative_votes')
        return _update_or_create_content(platform, comment, Comment, filters, comment_attrs, editable_fields)
    else:
        return None


def _cud_initiative_votes(platform, initiative):
    # Fetch initiative's votes
    connector = platform.connector
    url_cb = get_url_cb(connector, 'get_votes_cb')
    url = build_request_url(url_cb.url, url_cb.callback, {'initiative_id': initiative.external_id})
    resp = do_request(connector, url, url_cb.callback.method)
    votes = get_json_or_error(connector.name, url_cb.callback, resp)
    for vote in votes:
        author = _update_or_create_author(platform, {'id': vote['member_id']})
        parent_dict = _get_parent(platform, vote['parent_type'], vote['parent_id'])
        if parent_dict:
            if vote['parent_type'] == 'idea':
                campaign = parent_dict['parent_idea'].campaign
            else:
                campaign = parent_dict['parent_comment'].campaign
            vote_attrs = {'cp_id': vote['id'], 'source':'consultation_platform', 'datetime':vote['datetime'],
                          'initiative': initiative, 'campaign': campaign, 'value': vote['value'], 'author': author,
                          'source_consultation': platform}
            vote_attrs.update(parent_dict)
            vote_obj, vote_created = Vote.objects.get_or_create(cp_id=vote['id'], source_consultation=platform,
                                                                defaults=vote_attrs)
            if not vote_created:
                vote_obj.exist = True
                if vote_obj.value != vote['value']:
                    vote_obj.value = vote['value']
                    vote_obj.has_changed = True
                vote_obj.save()
        else:
            logger.error('Vote {} could\'nt be synchronized because its parent {} with id couldn\'t be found'.
                         format(vote['id'], vote['parent_type'], vote['parent_id']))


def _cud_initiative_comments(platform, initiative):
    # Fetch initiative's comments
    connector = platform.connector
    url_cb = get_url_cb(connector, 'get_comments_cb')
    url = build_request_url(url_cb.url, url_cb.callback, {'initiative_id': initiative.external_id})
    resp = do_request(connector, url, url_cb.callback.method)
    comments = get_json_or_error(connector.name, url_cb.callback, resp)
    delayed_comments = []
    # Iterate over initiative's comments
    for comment in comments:
        comment_obj = _do_create_update_comment(platform, initiative, comment)
        if not comment_obj:
            delayed_comments.append(comments)
    for delayed_comment in delayed_comments:
        comment_obj = _do_create_update_comment(platform, initiative, delayed_comment)
        if not comment_obj:
            logger.error('Comment {} couldn\'t be synchronized because its parent {} with id {} couldn\'t be found'.
                         format(delayed_comment['id'], delayed_comment['parent_type'], delayed_comment['parent_id']))


def _cud_initiative_ideas(platform, initiative):
    # Fetch ideas
    connector = platform.connector
    ideas_url_cb = get_url_cb(connector, 'get_ideas_cb')
    url = build_request_url(ideas_url_cb.url, ideas_url_cb.callback, {'initiative_id': initiative.external_id})
    resp = do_request(connector, url, ideas_url_cb.callback.method)
    ideas = get_json_or_error(connector.name, ideas_url_cb.callback, resp)
    # Iterate over initiative's ideas
    for idea in ideas:
        try:
            campaign = Campaign.objects.get(external_id=idea['campaign_info']['id'])
        except Campaign.DoesNotExist:
            logger.error('Couldn\'t find the campaign with the id {} within the initiative {}. '
                         'Idea {} cannot be synchronized.'.format(idea['campaign_info']['id'], initiative.name,
                                                                  idea['id']))
            continue
        filters = {'cp_id': idea['id'], 'source': 'consultation_platform'}
        idea_attrs = {'cp_id': idea['id'], 'source': 'consultation_platform', 'datetime': idea['datetime'],
                      'title': idea['title'], 'text': idea['text'], 'url': idea['url'], 'comments': idea['comments'],
                      'initiative': initiative, 'campaign': campaign, 'source_consultation': platform,
                      'positive_votes': idea['positive_votes'], 'negative_votes': idea['negative_votes']}
        editable_fields = ('title', 'text', 'comments', 'positive_votes', 'negative_votes')
        _update_or_create_content(platform, idea, Idea, filters, idea_attrs, editable_fields)
    # Should we delete ideas that don't exist anymore (those that conserve exist=False)?


def _invalidate_initiative_content(platform, initiative):
    # The invalidation process consist of assuming that all ideas, comments, and votes don't exist anymore
    # Then as they are obtained from the db they will be marked as still existing
    Idea.objects.filter(source_consultation=platform, initiative=initiative).update(exist=False)
    Comment.objects.filter(source_consultation=platform, initiative=initiative).update(exist=False)
    Vote.objects.filter(source_consultation=platform, initiative=initiative).update(exist=False)


# Lock is used to ensure that synchronization is only executed one at time
@shared_task
def synchronize_content():
    # The cache key consists of the task name and the MD5 digest
    # of the feed URL.
    hexdigest = md5('social_ideation').hexdigest()
    lock_id = '{0}-lock-{1}'.format('synchronize_content', hexdigest)

    # cache.add fails if the key already exists
    acquire_lock = lambda: cache.add(lock_id, 'true', 60 * 5)  # Lock expires in 5 minutes
    # memcache delete is very slow, but we have to use it to take
    # advantage of using add() for atomic locking
    release_lock = lambda: cache.delete(lock_id)

    if acquire_lock():
        logger.info('Starting synchronization...')
        try:
            for cplatform in ConsultationPlatform.objects.all():
                try:
                    initiatives = Initiative.objects.filter(platform=cplatform)
                    for initiative in initiatives:
                        if initiative.active:
                            logger.info('Synchronazing the content of the initiative {}'.format(initiative.name))
                            _invalidate_initiative_content(cplatform, initiative)
                            _cud_initiative_ideas(cplatform, initiative)
                            _cud_initiative_comments(cplatform, initiative)
                            _cud_initiative_votes(cplatform, initiative)
                except Initiative.DoesNotExist:
                    logger.error('Couldn\'t find initiatives associated to the platform {}. '
                                 'Content cannot be synchronized.'.format(cplatform.name))
        finally:
            release_lock()
    else:
        logger.info('The synchronization is already being executed by another worker')