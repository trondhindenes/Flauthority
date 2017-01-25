from flask_restful import Resource, Api
from flask_restful_swagger import swagger
from flauthority import app
from flauthority import api, app, celery, auth

from ModelClasses import AnsibleCommandModel, AnsiblePlaybookModel, AnsibleExtraArgsModel
import celery_runner



class TaskOutput(Resource):
    @swagger.operation(
    notes='Get the output of an Certificate generation task/job',
    nickname='taskoutput',
    parameters=[
        {
        "name": "task_id",
        "description": "The ID of the task/job to get status for",
        "required": True,
        "allowMultiple": False,
        "dataType": 'string',
        "paramType": "path"
        }
    ])
    @auth.login_required
    def get(self, task_id):
        task = celery_runner.generate_certificate.AsyncResult(task_id)

        if task.state == 'PENDING':
            result = "Task not found"
            resp = app.make_response((result, 404))
            return resp
        if task.state == "PROGRESS":
            result = task.info['output']
        else:
            if 'output' in task.info.keys():
                result = task.info['output']
            else:
                result = ""
        #result_out = task.info.replace('\n', "<br>")
        #result = result.replace('\n', '<br>')
        #return result, 200, {'Content-Type': 'text/html; charset=utf-8'}
        #resp = app.make_response((result, 200))
        #resp.headers['content-type'] = 'text/plain'
        return task.info

api.add_resource(TaskOutput, '/api/taskoutput/<string:task_id>')
