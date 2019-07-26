from flask import Flask, request
from flask_restful import Api, Resource
from prejudge_process import PrejudgeProcess


class Main(Resource):

    def get(self):
        return {
            "round": "/prejudge/test_round/id",
            "script": "/prejudge/test_round/id/test_script/id",
            "case": "/prejudge/test_round/id/test_script/id/test_case/id"
        }


class PrejudgeRound(Resource):

    def get(self, round_id):
        p = PrejudgeProcess(round_id=round_id)
        result = p.run()
        return result

    # def post(self, round_id):
    #     with open(os.path.join(os.getcwd(), "data", "response.json"), "r") as f:
    #         result = json.load(f)
    #     result["post_data"] = request.form["data"]
    #     return result


class PrejudgeScript(Resource):

    def get(self, round_id, script_id):
        p = PrejudgeProcess(round_id=round_id, script_id=script_id)
        result = p.run()
        return result


class PrejudgeCase(Resource):

    def get(self, round_id, script_id, case_id):
        p = PrejudgeProcess(round_id=round_id, script_id=script_id, case_id=case_id)
        result = p.run()
        return result


app = Flask(__name__)
api = Api(app)
api.add_resource(Main, "/prejudge/")
api.add_resource(PrejudgeRound, "/prejudge/test_round/<int:round_id>/")
api.add_resource(PrejudgeScript, "/prejudge/test_round/<int:round_id>/test_script/<int:script_id>/")
api.add_resource(PrejudgeCase, "/prejudge/test_round/<int:round_id>/test_script/<int:script_id>/test_case/<int:case_id>/")


if __name__ == '__main__':
    # app = Flask(__name__)
    # api = Api(app)
    # api.add_resource(Main, "/prejudge/")
    # api.add_resource(PrejudgeRound, "/prejudge/test_round/<int:round_id>/")
    # api.add_resource(PrejudgeScript, "/prejudge/test_round/<int:round_id>/test_script/<int:script_id>/")
    # api.add_resource(PrejudgeCase, "/prejudge/test_round/<int:round_id>/test_script/<int:script_id>/test_case/<int:case_id>/")

    # app.run("localhost", 8008, debug=True)
    app.run(host="127.0.0.1", port=8008)
