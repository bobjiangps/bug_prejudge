from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class PublicParameters(APIView):

    def get(self, request):
        data = {
            "pad": {
                "status": True,
                "dis": 0,
                "max": 200
            }
        }
        return Response(data, status=status.HTTP_200_OK)
