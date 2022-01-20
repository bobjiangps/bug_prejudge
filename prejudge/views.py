from prejudge_process import PrejudgeProcess
from rest_framework.views import APIView
from rest_framework.response import Response


class PrejudgeRound(APIView):

    def get(self, request, round_id):
        p = PrejudgeProcess(round_id=round_id)
        result = p.run()
        return Response(result)


class PrejudgeScript(APIView):

    def get(self, request, round_id, script_id):
        p = PrejudgeProcess(round_id=round_id, script_id=script_id)
        result = p.run()
        return Response(result)


class PrejudgeCase(APIView):

    def get(self, request, round_id, script_id, case_id):
        p = PrejudgeProcess(round_id=round_id, script_id=script_id, case_id=case_id)
        result = p.run()
        return Response(result)
