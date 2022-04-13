import logging
import subprocess
from django.http import JsonResponse
from multiprocessing import Process
from rest_framework.generics import GenericAPIView
from tools.permissions import ReviewPermission


logger = logging.getLogger('log')


def review(url):
    logger.info('Starting to review Pull Request')
    subprocess.call('python3 advisors/review_tool.py -u {} -c -l'.format(url), shell=True)


def edit_review(url, content):
    logger.info('Starting to edit review status')
    subprocess.call('python3 advisors/review_tool.py -u {} -e {} -l'.format(url, content), shell=True)


def base_log(pr_url, hook_name, action):
    logger.info('URL of Pull Request: {}'.format(pr_url))
    logger.info('Hook Name: {}'.format(hook_name))
    logger.info('Action: {}'.format(action))


class ReviewView(GenericAPIView):
    permission_classes = (ReviewPermission,)

    def post(self, request, *args, **kwargs):
        data = self.request.data
        try:
            hook_name = data['hook_name']
            action = data['action']
            pr_url = data['pull_request']['html_url']
        except (KeyError, TypeError):
            res = JsonResponse({'code': 400, 'msg': 'Bac Request'})
            res.status_code = 400
            return res

        if hook_name == 'merge_request_hooks' and action == 'open':
            base_log(pr_url, hook_name, action)
            logger.info('Notice Pull Request created')
            p1 = Process(target=review, args=(pr_url,))
            p1.start()
        elif hook_name == 'merge_request_hooks' and action == 'update':
            logger.info('Notice Pull Request update')
            try:
                action_desc = data['action_desc']
                logger.info('Action Description: {}'.format(action_desc))
                if action_desc == 'source_branch_changed':
                    base_log(pr_url, hook_name, action)
                    p2 = Process(target=review, args=(pr_url,))
                    p2.start()
                else:
                    logger.info('Notice no source branch changed, skip...')
            except KeyError:
                logger.info('Invaild update request, skip...')
        elif hook_name == 'note_hooks' and action == 'comment':
            base_log(pr_url, hook_name, action)
            logger.info('Notice Pull Request comment')
            comment = data['comment']['body']
            logger.info('Comment Body: {}'.format(comment))
            if comment.startswith('/review '):
                lines = comment.splitlines()
                try:
                    if len(lines) == 1 and lines[0].strip().split(maxsplit=1)[1] == "retrigger":
                        p3 = Process(target=review, args=(pr_url,))
                        p3.start()
                    else:
                        sets_li = []
                        for line in lines:
                            if line.strip().startswith("/review "):
                                sets = line.strip().split(maxsplit=1)[1]
                                sets_li.append(sets)
                        contents = " ".join(sets_li)
                        if contents:
                            logger.info(contents)
                            p4 = Process(target=edit_review, args=(pr_url, contents))
                            p4.start()
                except IndexError:
                    pass
        return JsonResponse({'code': 200, 'msg': 'OK'})
