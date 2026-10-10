from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework.views import APIView


@extend_schema(
    responses={200: inline_serializer("ApiRootResponse", fields={"data": serializers.DictField()})}
)
class ApiRootView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"data": {"name": "GrindBuddy API", "version": "v1"}})


@extend_schema(
    responses={200: inline_serializer("HealthCheckResponse", fields={"data": serializers.DictField()})}
)
class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"data": {"status": "ok"}})