"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.accounts.views import RefreshView, TokenView

urlpatterns = [
    path('api/v1/', include('apps.common.urls')),
    path('api/v1/', include('apps.accounts.urls')),
    path('api/v1/', include('apps.products.urls')),
    path('api/v1/', include('apps.partners.urls')),
    path('api/v1/', include('apps.purchases.urls')),
    path('api/v1/', include('apps.sales.urls')),
    path('api/v1/', include('apps.inventory.urls')),
    path('api/v1/', include('apps.reports.urls')),
    path('api/v1/', include('apps.system.urls')),
    path('api/v1/auth/token/', TokenView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/token/refresh/', RefreshView.as_view(), name='token_refresh'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
