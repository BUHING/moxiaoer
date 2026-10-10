/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ApiRootResponse } from '../models/ApiRootResponse';
import type { AttributeOptionListResponse } from '../models/AttributeOptionListResponse';
import type { AttributeOptionResponse } from '../models/AttributeOptionResponse';
import type { AttributeOptionWrite } from '../models/AttributeOptionWrite';
import type { CurrentUserResponse } from '../models/CurrentUserResponse';
import type { CustomerDeactivationResponse } from '../models/CustomerDeactivationResponse';
import type { CustomerListResponse } from '../models/CustomerListResponse';
import type { CustomerResponse } from '../models/CustomerResponse';
import type { CustomerWrite } from '../models/CustomerWrite';
import type { DashboardResponse } from '../models/DashboardResponse';
import type { DeactivationResponse } from '../models/DeactivationResponse';
import type { EmployeeCreate } from '../models/EmployeeCreate';
import type { EmployeeListResponse } from '../models/EmployeeListResponse';
import type { EmployeeResponse } from '../models/EmployeeResponse';
import type { HealthCheckResponse } from '../models/HealthCheckResponse';
import type { InventoryReportResponse } from '../models/InventoryReportResponse';
import type { LabelTemplateListResponse } from '../models/LabelTemplateListResponse';
import type { LabelTemplateResponse } from '../models/LabelTemplateResponse';
import type { LabelTemplateWrite } from '../models/LabelTemplateWrite';
import type { PasswordResetConfirm } from '../models/PasswordResetConfirm';
import type { PasswordResetRequest } from '../models/PasswordResetRequest';
import type { PatchedAttributeOptionWrite } from '../models/PatchedAttributeOptionWrite';
import type { PatchedCustomerWrite } from '../models/PatchedCustomerWrite';
import type { PatchedEmployeeUpdate } from '../models/PatchedEmployeeUpdate';
import type { PatchedLabelTemplateWrite } from '../models/PatchedLabelTemplateWrite';
import type { PatchedPriceLevelWrite } from '../models/PatchedPriceLevelWrite';
import type { PatchedProductAttributeWrite } from '../models/PatchedProductAttributeWrite';
import type { PatchedProductWrite } from '../models/PatchedProductWrite';
import type { PatchedPurchaseDocumentWrite } from '../models/PatchedPurchaseDocumentWrite';
import type { PatchedPurchaseReturnWrite } from '../models/PatchedPurchaseReturnWrite';
import type { PatchedSalesDocumentWrite } from '../models/PatchedSalesDocumentWrite';
import type { PatchedSpecificationWrite } from '../models/PatchedSpecificationWrite';
import type { PatchedSupplierWrite } from '../models/PatchedSupplierWrite';
import type { PatchedUnitWrite } from '../models/PatchedUnitWrite';
import type { PermissionRequestCreate } from '../models/PermissionRequestCreate';
import type { PermissionRequestListResponse } from '../models/PermissionRequestListResponse';
import type { PermissionRequestResponse } from '../models/PermissionRequestResponse';
import type { PriceLevelListResponse } from '../models/PriceLevelListResponse';
import type { PriceLevelResponse } from '../models/PriceLevelResponse';
import type { PriceLevelWrite } from '../models/PriceLevelWrite';
import type { ProductAttributeListResponse } from '../models/ProductAttributeListResponse';
import type { ProductAttributeResponse } from '../models/ProductAttributeResponse';
import type { ProductAttributeWrite } from '../models/ProductAttributeWrite';
import type { ProductListResponse } from '../models/ProductListResponse';
import type { ProductPriceListResponse } from '../models/ProductPriceListResponse';
import type { ProductResponse } from '../models/ProductResponse';
import type { ProductWrite } from '../models/ProductWrite';
import type { PurchaseDocumentWrite } from '../models/PurchaseDocumentWrite';
import type { PurchaseListResponse } from '../models/PurchaseListResponse';
import type { PurchaseReportResponse } from '../models/PurchaseReportResponse';
import type { PurchaseResponse } from '../models/PurchaseResponse';
import type { PurchaseReturnListResponse } from '../models/PurchaseReturnListResponse';
import type { PurchaseReturnResponse } from '../models/PurchaseReturnResponse';
import type { PurchaseReturnWrite } from '../models/PurchaseReturnWrite';
import type { RefreshResponse } from '../models/RefreshResponse';
import type { Register } from '../models/Register';
import type { SalesDocumentWrite } from '../models/SalesDocumentWrite';
import type { SalesOrderListResponse } from '../models/SalesOrderListResponse';
import type { SalesOrderResponse } from '../models/SalesOrderResponse';
import type { SalesReportResponse } from '../models/SalesReportResponse';
import type { SalesReturnListResponse } from '../models/SalesReturnListResponse';
import type { SalesReturnResponse } from '../models/SalesReturnResponse';
import type { ShopProfile } from '../models/ShopProfile';
import type { ShopProfileResponse } from '../models/ShopProfileResponse';
import type { SpecificationListResponse } from '../models/SpecificationListResponse';
import type { SpecificationResponse } from '../models/SpecificationResponse';
import type { SpecificationWrite } from '../models/SpecificationWrite';
import type { StockBalanceListResponse } from '../models/StockBalanceListResponse';
import type { StockMovementListResponse } from '../models/StockMovementListResponse';
import type { SupplierDeactivationResponse } from '../models/SupplierDeactivationResponse';
import type { SupplierListResponse } from '../models/SupplierListResponse';
import type { SupplierResponse } from '../models/SupplierResponse';
import type { SupplierWrite } from '../models/SupplierWrite';
import type { TokenLogin } from '../models/TokenLogin';
import type { TokenRefreshInput } from '../models/TokenRefreshInput';
import type { TokenResponse } from '../models/TokenResponse';
import type { UnitListResponse } from '../models/UnitListResponse';
import type { UnitResponse } from '../models/UnitResponse';
import type { UnitWrite } from '../models/UnitWrite';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class V1Service {
    /**
     * @returns ApiRootResponse
     * @throws ApiError
     */
    public static v1Retrieve(): CancelablePromise<ApiRootResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/',
        });
    }
    /**
     * @returns CurrentUserResponse
     * @throws ApiError
     */
    public static v1AuthMeRetrieve(): CancelablePromise<CurrentUserResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/auth/me/',
        });
    }
    /**
     * @param requestBody
     * @returns void
     * @throws ApiError
     */
    public static v1AuthPasswordResetCreate(
        requestBody: PasswordResetRequest,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/auth/password-reset/',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param requestBody
     * @returns void
     * @throws ApiError
     */
    public static v1AuthPasswordResetConfirmCreate(
        requestBody: PasswordResetConfirm,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/auth/password-reset/confirm/',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param requestBody
     * @returns CurrentUserResponse
     * @throws ApiError
     */
    public static v1AuthRegisterCreate(
        requestBody: Register,
    ): CancelablePromise<CurrentUserResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/auth/register/',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Takes a set of user credentials and returns an access and refresh JSON web
     * token pair to prove the authentication of those credentials.
     * @param requestBody
     * @returns TokenResponse
     * @throws ApiError
     */
    public static v1AuthTokenCreate(
        requestBody: TokenLogin,
    ): CancelablePromise<TokenResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/auth/token/',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Takes a refresh type JSON web token and returns an access type JSON web
     * token if the refresh token is valid.
     * @param requestBody
     * @returns RefreshResponse
     * @throws ApiError
     */
    public static v1AuthTokenRefreshCreate(
        requestBody: TokenRefreshInput,
    ): CancelablePromise<RefreshResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/auth/token/refresh/',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param isActive
     * @param page
     * @param pageSize
     * @param search
     * @returns CustomerListResponse
     * @throws ApiError
     */
    public static customersList(
        isActive?: boolean,
        page?: number,
        pageSize?: number,
        search?: string,
    ): CancelablePromise<CustomerListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/customers/',
            query: {
                'is_active': isActive,
                'page': page,
                'page_size': pageSize,
                'search': search,
            },
        });
    }
    /**
     * @param requestBody
     * @returns CustomerResponse
     * @throws ApiError
     */
    public static customersCreate(
        requestBody?: CustomerWrite,
    ): CancelablePromise<CustomerResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/customers/',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param customerId
     * @returns CustomerResponse
     * @throws ApiError
     */
    public static customersRetrieve(
        customerId: string,
    ): CancelablePromise<CustomerResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/customers/{customer_id}/',
            path: {
                'customer_id': customerId,
            },
        });
    }
    /**
     * @param customerId
     * @param requestBody
     * @returns CustomerResponse
     * @throws ApiError
     */
    public static customersPartialUpdate(
        customerId: string,
        requestBody?: PatchedCustomerWrite,
    ): CancelablePromise<CustomerResponse> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/customers/{customer_id}/',
            path: {
                'customer_id': customerId,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param customerId
     * @returns void
     * @throws ApiError
     */
    public static customersDestroy(
        customerId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/customers/{customer_id}/',
            path: {
                'customer_id': customerId,
            },
        });
    }
    /**
     * @param customerId
     * @returns CustomerDeactivationResponse
     * @throws ApiError
     */
    public static customersDeactivate(
        customerId: string,
    ): CancelablePromise<CustomerDeactivationResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/customers/{customer_id}/deactivate/',
            path: {
                'customer_id': customerId,
            },
        });
    }
    /**
     * @returns DashboardResponse
     * @throws ApiError
     */
    public static dashboardRetrieve(): CancelablePromise<DashboardResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/dashboard/',
        });
    }
    /**
     * @returns EmployeeListResponse
     * @throws ApiError
     */
    public static employeesList(): CancelablePromise<EmployeeListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/employees/',
        });
    }
    /**
     * @param requestBody
     * @returns EmployeeResponse
     * @throws ApiError
     */
    public static employeesCreate(
        requestBody: EmployeeCreate,
    ): CancelablePromise<EmployeeResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/employees/',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param userId
     * @returns EmployeeResponse
     * @throws ApiError
     */
    public static employeesRetrieve(
        userId: string,
    ): CancelablePromise<EmployeeResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/employees/{user_id}/',
            path: {
                'user_id': userId,
            },
        });
    }
    /**
     * @param userId
     * @param requestBody
     * @returns EmployeeResponse
     * @throws ApiError
     */
    public static employeesPartialUpdate(
        userId: string,
        requestBody?: PatchedEmployeeUpdate,
    ): CancelablePromise<EmployeeResponse> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/employees/{user_id}/',
            path: {
                'user_id': userId,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @returns HealthCheckResponse
     * @throws ApiError
     */
    public static v1HealthRetrieve(): CancelablePromise<HealthCheckResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/health/',
        });
    }
    /**
     * @param page
     * @param pageSize
     * @param productId
     * @param search
     * @returns StockBalanceListResponse
     * @throws ApiError
     */
    public static inventoryBalancesList(
        page?: number,
        pageSize?: number,
        productId?: string,
        search?: string,
    ): CancelablePromise<StockBalanceListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/inventory/balances/',
            query: {
                'page': page,
                'page_size': pageSize,
                'product_id': productId,
                'search': search,
            },
        });
    }
    /**
     * @param dateFrom
     * @param dateTo
     * @param movementType
     * @param page
     * @param pageSize
     * @param productId
     * @param search
     * @returns StockMovementListResponse
     * @throws ApiError
     */
    public static inventoryMovementsList(
        dateFrom?: string,
        dateTo?: string,
        movementType?: 'INITIAL' | 'PURCHASE' | 'PURCHASE_RETURN' | 'SALE' | 'SALE_RETURN',
        page?: number,
        pageSize?: number,
        productId?: string,
        search?: string,
    ): CancelablePromise<StockMovementListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/inventory/movements/',
            query: {
                'date_from': dateFrom,
                'date_to': dateTo,
                'movement_type': movementType,
                'page': page,
                'page_size': pageSize,
                'product_id': productId,
                'search': search,
            },
        });
    }
    /**
     * @returns LabelTemplateListResponse
     * @throws ApiError
     */
    public static labelTemplatesList(): CancelablePromise<LabelTemplateListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/label-templates/',
        });
    }
    /**
     * @param requestBody
     * @returns LabelTemplateResponse
     * @throws ApiError
     */
    public static labelTemplatesCreate(
        requestBody: LabelTemplateWrite,
    ): CancelablePromise<LabelTemplateResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/label-templates/',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param templateId
     * @returns LabelTemplateResponse
     * @throws ApiError
     */
    public static labelTemplatesRetrieve(
        templateId: string,
    ): CancelablePromise<LabelTemplateResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/label-templates/{template_id}/',
            path: {
                'template_id': templateId,
            },
        });
    }
    /**
     * @param templateId
     * @param requestBody
     * @returns LabelTemplateResponse
     * @throws ApiError
     */
    public static labelTemplatesPartialUpdate(
        templateId: string,
        requestBody?: PatchedLabelTemplateWrite,
    ): CancelablePromise<LabelTemplateResponse> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/label-templates/{template_id}/',
            path: {
                'template_id': templateId,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @returns PermissionRequestListResponse
     * @throws ApiError
     */
    public static permissionRequestsList(): CancelablePromise<PermissionRequestListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/permission-requests/',
        });
    }
    /**
     * @param requestBody
     * @returns PermissionRequestResponse
     * @throws ApiError
     */
    public static permissionRequestsCreate(
        requestBody: PermissionRequestCreate,
    ): CancelablePromise<PermissionRequestResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/permission-requests/',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param requestId
     * @returns PermissionRequestResponse
     * @throws ApiError
     */
    public static v1PermissionRequestsApproveCreate(
        requestId: string,
    ): CancelablePromise<PermissionRequestResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/permission-requests/{request_id}/approve/',
            path: {
                'request_id': requestId,
            },
        });
    }
    /**
     * @param requestId
     * @returns PermissionRequestResponse
     * @throws ApiError
     */
    public static v1PermissionRequestsRejectCreate(
        requestId: string,
    ): CancelablePromise<PermissionRequestResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/permission-requests/{request_id}/reject/',
            path: {
                'request_id': requestId,
            },
        });
    }
    /**
     * @param page
     * @param pageSize
     * @returns PriceLevelListResponse
     * @throws ApiError
     */
    public static priceLevelsList(
        page?: number,
        pageSize?: number,
    ): CancelablePromise<PriceLevelListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/price-levels/',
            query: {
                'page': page,
                'page_size': pageSize,
            },
        });
    }
    /**
     * @param requestBody
     * @returns PriceLevelResponse
     * @throws ApiError
     */
    public static priceLevelsCreate(
        requestBody?: PriceLevelWrite,
    ): CancelablePromise<PriceLevelResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/price-levels/',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param resourceId
     * @returns PriceLevelResponse
     * @throws ApiError
     */
    public static priceLevelsRetrieve(
        resourceId: string,
    ): CancelablePromise<PriceLevelResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/price-levels/{resource_id}/',
            path: {
                'resource_id': resourceId,
            },
        });
    }
    /**
     * @param resourceId
     * @param requestBody
     * @returns PriceLevelResponse
     * @throws ApiError
     */
    public static priceLevelsPartialUpdate(
        resourceId: string,
        requestBody?: PatchedPriceLevelWrite,
    ): CancelablePromise<PriceLevelResponse> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/price-levels/{resource_id}/',
            path: {
                'resource_id': resourceId,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param resourceId
     * @returns void
     * @throws ApiError
     */
    public static priceLevelsDestroy(
        resourceId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/price-levels/{resource_id}/',
            path: {
                'resource_id': resourceId,
            },
        });
    }
    /**
     * @param resourceId
     * @returns DeactivationResponse
     * @throws ApiError
     */
    public static v1PriceLevelsDeactivateCreate(
        resourceId: string,
    ): CancelablePromise<DeactivationResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/price-levels/{resource_id}/deactivate/',
            path: {
                'resource_id': resourceId,
            },
        });
    }
    /**
     * @param page
     * @param pageSize
     * @returns ProductAttributeListResponse
     * @throws ApiError
     */
    public static productAttributesList(
        page?: number,
        pageSize?: number,
    ): CancelablePromise<ProductAttributeListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/product-attributes/',
            query: {
                'page': page,
                'page_size': pageSize,
            },
        });
    }
    /**
     * @param requestBody
     * @returns ProductAttributeResponse
     * @throws ApiError
     */
    public static productAttributesCreate(
        requestBody?: ProductAttributeWrite,
    ): CancelablePromise<ProductAttributeResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/product-attributes/',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param attributeId
     * @param page
     * @param pageSize
     * @returns AttributeOptionListResponse
     * @throws ApiError
     */
    public static productAttributeOptionsList(
        attributeId: string,
        page?: number,
        pageSize?: number,
    ): CancelablePromise<AttributeOptionListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/product-attributes/{attribute_id}/options/',
            path: {
                'attribute_id': attributeId,
            },
            query: {
                'page': page,
                'page_size': pageSize,
            },
        });
    }
    /**
     * @param attributeId
     * @param requestBody
     * @returns AttributeOptionResponse
     * @throws ApiError
     */
    public static productAttributeOptionsCreate(
        attributeId: string,
        requestBody?: AttributeOptionWrite,
    ): CancelablePromise<AttributeOptionResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/product-attributes/{attribute_id}/options/',
            path: {
                'attribute_id': attributeId,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param attributeId
     * @param optionId
     * @param requestBody
     * @returns AttributeOptionResponse
     * @throws ApiError
     */
    public static productAttributeOptionsPartialUpdate(
        attributeId: string,
        optionId: string,
        requestBody?: PatchedAttributeOptionWrite,
    ): CancelablePromise<AttributeOptionResponse> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/product-attributes/{attribute_id}/options/{option_id}/',
            path: {
                'attribute_id': attributeId,
                'option_id': optionId,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param attributeId
     * @param optionId
     * @returns void
     * @throws ApiError
     */
    public static productAttributeOptionsDestroy(
        attributeId: string,
        optionId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/product-attributes/{attribute_id}/options/{option_id}/',
            path: {
                'attribute_id': attributeId,
                'option_id': optionId,
            },
        });
    }
    /**
     * @param resourceId
     * @returns ProductAttributeResponse
     * @throws ApiError
     */
    public static productAttributesRetrieve(
        resourceId: string,
    ): CancelablePromise<ProductAttributeResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/product-attributes/{resource_id}/',
            path: {
                'resource_id': resourceId,
            },
        });
    }
    /**
     * @param resourceId
     * @param requestBody
     * @returns ProductAttributeResponse
     * @throws ApiError
     */
    public static productAttributesPartialUpdate(
        resourceId: string,
        requestBody?: PatchedProductAttributeWrite,
    ): CancelablePromise<ProductAttributeResponse> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/product-attributes/{resource_id}/',
            path: {
                'resource_id': resourceId,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param resourceId
     * @returns void
     * @throws ApiError
     */
    public static productAttributesDestroy(
        resourceId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/product-attributes/{resource_id}/',
            path: {
                'resource_id': resourceId,
            },
        });
    }
    /**
     * @param resourceId
     * @returns DeactivationResponse
     * @throws ApiError
     */
    public static v1ProductAttributesDeactivateCreate(
        resourceId: string,
    ): CancelablePromise<DeactivationResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/product-attributes/{resource_id}/deactivate/',
            path: {
                'resource_id': resourceId,
            },
        });
    }
    /**
     * @param isActive
     * @param page
     * @param pageSize
     * @param priceLevelId
     * @param search
     * @param unitId
     * @returns ProductListResponse
     * @throws ApiError
     */
    public static productsList(
        isActive?: boolean,
        page?: number,
        pageSize?: number,
        priceLevelId?: string,
        search?: string,
        unitId?: string,
    ): CancelablePromise<ProductListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/products/',
            query: {
                'is_active': isActive,
                'page': page,
                'page_size': pageSize,
                'price_level_id': priceLevelId,
                'search': search,
                'unit_id': unitId,
            },
        });
    }
    /**
     * @param requestBody
     * @returns ProductResponse
     * @throws ApiError
     */
    public static productsCreate(
        requestBody?: ProductWrite,
    ): CancelablePromise<ProductResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/products/',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param productId
     * @returns ProductResponse
     * @throws ApiError
     */
    public static productsRetrieve(
        productId: string,
    ): CancelablePromise<ProductResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/products/{product_id}/',
            path: {
                'product_id': productId,
            },
        });
    }
    /**
     * @param productId
     * @param requestBody
     * @returns ProductResponse
     * @throws ApiError
     */
    public static productsPartialUpdate(
        productId: string,
        requestBody?: PatchedProductWrite,
    ): CancelablePromise<ProductResponse> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/products/{product_id}/',
            path: {
                'product_id': productId,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param productId
     * @returns void
     * @throws ApiError
     */
    public static productsDestroy(
        productId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/products/{product_id}/',
            path: {
                'product_id': productId,
            },
        });
    }
    /**
     * @param productId
     * @returns ProductPriceListResponse
     * @throws ApiError
     */
    public static productPricesList(
        productId: string,
    ): CancelablePromise<ProductPriceListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/products/{product_id}/prices/',
            path: {
                'product_id': productId,
            },
        });
    }
    /**
     * @param resourceId
     * @returns DeactivationResponse
     * @throws ApiError
     */
    public static v1ProductsDeactivateCreate(
        resourceId: string,
    ): CancelablePromise<DeactivationResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/products/{resource_id}/deactivate/',
            path: {
                'resource_id': resourceId,
            },
        });
    }
    /**
     * @param page
     * @param pageSize
     * @param status
     * @param supplierId
     * @returns PurchaseReturnListResponse
     * @throws ApiError
     */
    public static purchaseReturnsList(
        page?: number,
        pageSize?: number,
        status?: string,
        supplierId?: string,
    ): CancelablePromise<PurchaseReturnListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/purchase-returns/',
            query: {
                'page': page,
                'page_size': pageSize,
                'status': status,
                'supplier_id': supplierId,
            },
        });
    }
    /**
     * @param requestBody
     * @returns PurchaseReturnResponse
     * @throws ApiError
     */
    public static purchaseReturnsCreate(
        requestBody?: PurchaseReturnWrite,
    ): CancelablePromise<PurchaseReturnResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/purchase-returns/',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param documentId
     * @param page
     * @param pageSize
     * @param status
     * @param supplierId
     * @returns PurchaseReturnResponse
     * @throws ApiError
     */
    public static purchaseReturnsRetrieve(
        documentId: string,
        page?: number,
        pageSize?: number,
        status?: string,
        supplierId?: string,
    ): CancelablePromise<PurchaseReturnResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/purchase-returns/{document_id}/',
            path: {
                'document_id': documentId,
            },
            query: {
                'page': page,
                'page_size': pageSize,
                'status': status,
                'supplier_id': supplierId,
            },
        });
    }
    /**
     * @param documentId
     * @param requestBody
     * @returns PurchaseReturnResponse
     * @throws ApiError
     */
    public static purchaseReturnsPartialUpdate(
        documentId: string,
        requestBody?: PatchedPurchaseReturnWrite,
    ): CancelablePromise<PurchaseReturnResponse> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/purchase-returns/{document_id}/',
            path: {
                'document_id': documentId,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param documentId
     * @returns void
     * @throws ApiError
     */
    public static purchaseReturnsDelete(
        documentId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/purchase-returns/{document_id}/',
            path: {
                'document_id': documentId,
            },
        });
    }
    /**
     * @param idempotencyKey
     * @param documentId
     * @returns PurchaseReturnResponse
     * @throws ApiError
     */
    public static purchaseReturnsComplete(
        idempotencyKey: string,
        documentId: string,
    ): CancelablePromise<PurchaseReturnResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/purchase-returns/{document_id}/complete/',
            path: {
                'document_id': documentId,
            },
            headers: {
                'Idempotency-Key': idempotencyKey,
            },
        });
    }
    /**
     * @param page
     * @param pageSize
     * @param status
     * @param supplierId
     * @returns PurchaseListResponse
     * @throws ApiError
     */
    public static purchasesList(
        page?: number,
        pageSize?: number,
        status?: string,
        supplierId?: string,
    ): CancelablePromise<PurchaseListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/purchases/',
            query: {
                'page': page,
                'page_size': pageSize,
                'status': status,
                'supplier_id': supplierId,
            },
        });
    }
    /**
     * @param requestBody
     * @returns PurchaseResponse
     * @throws ApiError
     */
    public static purchasesCreate(
        requestBody?: PurchaseDocumentWrite,
    ): CancelablePromise<PurchaseResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/purchases/',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param documentId
     * @param page
     * @param pageSize
     * @param status
     * @param supplierId
     * @returns PurchaseResponse
     * @throws ApiError
     */
    public static purchasesRetrieve(
        documentId: string,
        page?: number,
        pageSize?: number,
        status?: string,
        supplierId?: string,
    ): CancelablePromise<PurchaseResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/purchases/{document_id}/',
            path: {
                'document_id': documentId,
            },
            query: {
                'page': page,
                'page_size': pageSize,
                'status': status,
                'supplier_id': supplierId,
            },
        });
    }
    /**
     * @param documentId
     * @param requestBody
     * @returns PurchaseResponse
     * @throws ApiError
     */
    public static purchasesPartialUpdate(
        documentId: string,
        requestBody?: PatchedPurchaseDocumentWrite,
    ): CancelablePromise<PurchaseResponse> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/purchases/{document_id}/',
            path: {
                'document_id': documentId,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param documentId
     * @returns void
     * @throws ApiError
     */
    public static purchasesDelete(
        documentId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/purchases/{document_id}/',
            path: {
                'document_id': documentId,
            },
        });
    }
    /**
     * @param idempotencyKey
     * @param documentId
     * @returns PurchaseResponse
     * @throws ApiError
     */
    public static purchasesComplete(
        idempotencyKey: string,
        documentId: string,
    ): CancelablePromise<PurchaseResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/purchases/{document_id}/complete/',
            path: {
                'document_id': documentId,
            },
            headers: {
                'Idempotency-Key': idempotencyKey,
            },
        });
    }
    /**
     * @returns InventoryReportResponse
     * @throws ApiError
     */
    public static reportsInventoryRetrieve(): CancelablePromise<InventoryReportResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/reports/inventory/',
        });
    }
    /**
     * @param dateFrom
     * @param dateTo
     * @returns PurchaseReportResponse
     * @throws ApiError
     */
    public static reportsPurchasesRetrieve(
        dateFrom?: string,
        dateTo?: string,
    ): CancelablePromise<PurchaseReportResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/reports/purchases/',
            query: {
                'date_from': dateFrom,
                'date_to': dateTo,
            },
        });
    }
    /**
     * @param dateFrom
     * @param dateTo
     * @returns SalesReportResponse
     * @throws ApiError
     */
    public static reportsSalesRetrieve(
        dateFrom?: string,
        dateTo?: string,
    ): CancelablePromise<SalesReportResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/reports/sales/',
            query: {
                'date_from': dateFrom,
                'date_to': dateTo,
            },
        });
    }
    /**
     * @param customerId
     * @param page
     * @param pageSize
     * @param status
     * @returns SalesOrderListResponse
     * @throws ApiError
     */
    public static salesOrdersList(
        customerId?: string,
        page?: number,
        pageSize?: number,
        status?: string,
    ): CancelablePromise<SalesOrderListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/sales-orders/',
            query: {
                'customer_id': customerId,
                'page': page,
                'page_size': pageSize,
                'status': status,
            },
        });
    }
    /**
     * @param requestBody
     * @returns SalesOrderResponse
     * @throws ApiError
     */
    public static salesOrdersCreate(
        requestBody?: SalesDocumentWrite,
    ): CancelablePromise<SalesOrderResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/sales-orders/',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param documentId
     * @param customerId
     * @param page
     * @param pageSize
     * @param status
     * @returns SalesOrderResponse
     * @throws ApiError
     */
    public static salesOrdersRetrieve(
        documentId: string,
        customerId?: string,
        page?: number,
        pageSize?: number,
        status?: string,
    ): CancelablePromise<SalesOrderResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/sales-orders/{document_id}/',
            path: {
                'document_id': documentId,
            },
            query: {
                'customer_id': customerId,
                'page': page,
                'page_size': pageSize,
                'status': status,
            },
        });
    }
    /**
     * @param documentId
     * @param requestBody
     * @returns SalesOrderResponse
     * @throws ApiError
     */
    public static salesOrdersPartialUpdate(
        documentId: string,
        requestBody?: PatchedSalesDocumentWrite,
    ): CancelablePromise<SalesOrderResponse> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/sales-orders/{document_id}/',
            path: {
                'document_id': documentId,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param documentId
     * @returns void
     * @throws ApiError
     */
    public static salesOrdersDelete(
        documentId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/sales-orders/{document_id}/',
            path: {
                'document_id': documentId,
            },
        });
    }
    /**
     * @param idempotencyKey
     * @param documentId
     * @returns SalesOrderResponse
     * @throws ApiError
     */
    public static salesOrdersComplete(
        idempotencyKey: string,
        documentId: string,
    ): CancelablePromise<SalesOrderResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/sales-orders/{document_id}/complete/',
            path: {
                'document_id': documentId,
            },
            headers: {
                'Idempotency-Key': idempotencyKey,
            },
        });
    }
    /**
     * @param customerId
     * @param page
     * @param pageSize
     * @param status
     * @returns SalesReturnListResponse
     * @throws ApiError
     */
    public static salesReturnsList(
        customerId?: string,
        page?: number,
        pageSize?: number,
        status?: string,
    ): CancelablePromise<SalesReturnListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/sales-returns/',
            query: {
                'customer_id': customerId,
                'page': page,
                'page_size': pageSize,
                'status': status,
            },
        });
    }
    /**
     * @param requestBody
     * @returns SalesReturnResponse
     * @throws ApiError
     */
    public static salesReturnsCreate(
        requestBody?: SalesDocumentWrite,
    ): CancelablePromise<SalesReturnResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/sales-returns/',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param documentId
     * @param customerId
     * @param page
     * @param pageSize
     * @param status
     * @returns SalesReturnResponse
     * @throws ApiError
     */
    public static salesReturnsRetrieve(
        documentId: string,
        customerId?: string,
        page?: number,
        pageSize?: number,
        status?: string,
    ): CancelablePromise<SalesReturnResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/sales-returns/{document_id}/',
            path: {
                'document_id': documentId,
            },
            query: {
                'customer_id': customerId,
                'page': page,
                'page_size': pageSize,
                'status': status,
            },
        });
    }
    /**
     * @param documentId
     * @param requestBody
     * @returns SalesReturnResponse
     * @throws ApiError
     */
    public static salesReturnsPartialUpdate(
        documentId: string,
        requestBody?: PatchedSalesDocumentWrite,
    ): CancelablePromise<SalesReturnResponse> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/sales-returns/{document_id}/',
            path: {
                'document_id': documentId,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param documentId
     * @returns void
     * @throws ApiError
     */
    public static salesReturnsDelete(
        documentId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/sales-returns/{document_id}/',
            path: {
                'document_id': documentId,
            },
        });
    }
    /**
     * @param idempotencyKey
     * @param documentId
     * @returns SalesReturnResponse
     * @throws ApiError
     */
    public static salesReturnsComplete(
        idempotencyKey: string,
        documentId: string,
    ): CancelablePromise<SalesReturnResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/sales-returns/{document_id}/complete/',
            path: {
                'document_id': documentId,
            },
            headers: {
                'Idempotency-Key': idempotencyKey,
            },
        });
    }
    /**
     * @returns ShopProfileResponse
     * @throws ApiError
     */
    public static shopProfileRetrieve(): CancelablePromise<ShopProfileResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/shop-profile/',
        });
    }
    /**
     * @param requestBody
     * @returns ShopProfileResponse
     * @throws ApiError
     */
    public static shopProfileUpdate(
        requestBody: ShopProfile,
    ): CancelablePromise<ShopProfileResponse> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/shop-profile/',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param page
     * @param pageSize
     * @returns SpecificationListResponse
     * @throws ApiError
     */
    public static specificationsList(
        page?: number,
        pageSize?: number,
    ): CancelablePromise<SpecificationListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/specifications/',
            query: {
                'page': page,
                'page_size': pageSize,
            },
        });
    }
    /**
     * @param requestBody
     * @returns SpecificationResponse
     * @throws ApiError
     */
    public static specificationsCreate(
        requestBody?: SpecificationWrite,
    ): CancelablePromise<SpecificationResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/specifications/',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param resourceId
     * @returns SpecificationResponse
     * @throws ApiError
     */
    public static specificationsRetrieve(
        resourceId: string,
    ): CancelablePromise<SpecificationResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/specifications/{resource_id}/',
            path: {
                'resource_id': resourceId,
            },
        });
    }
    /**
     * @param resourceId
     * @param requestBody
     * @returns SpecificationResponse
     * @throws ApiError
     */
    public static specificationsPartialUpdate(
        resourceId: string,
        requestBody?: PatchedSpecificationWrite,
    ): CancelablePromise<SpecificationResponse> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/specifications/{resource_id}/',
            path: {
                'resource_id': resourceId,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param resourceId
     * @returns void
     * @throws ApiError
     */
    public static specificationsDestroy(
        resourceId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/specifications/{resource_id}/',
            path: {
                'resource_id': resourceId,
            },
        });
    }
    /**
     * @param resourceId
     * @returns DeactivationResponse
     * @throws ApiError
     */
    public static v1SpecificationsDeactivateCreate(
        resourceId: string,
    ): CancelablePromise<DeactivationResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/specifications/{resource_id}/deactivate/',
            path: {
                'resource_id': resourceId,
            },
        });
    }
    /**
     * @param isActive
     * @param page
     * @param pageSize
     * @param search
     * @returns SupplierListResponse
     * @throws ApiError
     */
    public static suppliersList(
        isActive?: boolean,
        page?: number,
        pageSize?: number,
        search?: string,
    ): CancelablePromise<SupplierListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/suppliers/',
            query: {
                'is_active': isActive,
                'page': page,
                'page_size': pageSize,
                'search': search,
            },
        });
    }
    /**
     * @param requestBody
     * @returns SupplierResponse
     * @throws ApiError
     */
    public static suppliersCreate(
        requestBody?: SupplierWrite,
    ): CancelablePromise<SupplierResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/suppliers/',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param supplierId
     * @returns SupplierResponse
     * @throws ApiError
     */
    public static suppliersRetrieve(
        supplierId: string,
    ): CancelablePromise<SupplierResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/suppliers/{supplier_id}/',
            path: {
                'supplier_id': supplierId,
            },
        });
    }
    /**
     * @param supplierId
     * @param requestBody
     * @returns SupplierResponse
     * @throws ApiError
     */
    public static suppliersPartialUpdate(
        supplierId: string,
        requestBody?: PatchedSupplierWrite,
    ): CancelablePromise<SupplierResponse> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/suppliers/{supplier_id}/',
            path: {
                'supplier_id': supplierId,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param supplierId
     * @returns void
     * @throws ApiError
     */
    public static suppliersDestroy(
        supplierId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/suppliers/{supplier_id}/',
            path: {
                'supplier_id': supplierId,
            },
        });
    }
    /**
     * @param supplierId
     * @returns SupplierDeactivationResponse
     * @throws ApiError
     */
    public static suppliersDeactivate(
        supplierId: string,
    ): CancelablePromise<SupplierDeactivationResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/suppliers/{supplier_id}/deactivate/',
            path: {
                'supplier_id': supplierId,
            },
        });
    }
    /**
     * @param page
     * @param pageSize
     * @returns UnitListResponse
     * @throws ApiError
     */
    public static unitsList(
        page?: number,
        pageSize?: number,
    ): CancelablePromise<UnitListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/units/',
            query: {
                'page': page,
                'page_size': pageSize,
            },
        });
    }
    /**
     * @param requestBody
     * @returns UnitResponse
     * @throws ApiError
     */
    public static unitsCreate(
        requestBody?: UnitWrite,
    ): CancelablePromise<UnitResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/units/',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param resourceId
     * @returns UnitResponse
     * @throws ApiError
     */
    public static unitsRetrieve(
        resourceId: string,
    ): CancelablePromise<UnitResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/units/{resource_id}/',
            path: {
                'resource_id': resourceId,
            },
        });
    }
    /**
     * @param resourceId
     * @param requestBody
     * @returns UnitResponse
     * @throws ApiError
     */
    public static unitsPartialUpdate(
        resourceId: string,
        requestBody?: PatchedUnitWrite,
    ): CancelablePromise<UnitResponse> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/units/{resource_id}/',
            path: {
                'resource_id': resourceId,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param resourceId
     * @returns void
     * @throws ApiError
     */
    public static unitsDestroy(
        resourceId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/units/{resource_id}/',
            path: {
                'resource_id': resourceId,
            },
        });
    }
    /**
     * @param resourceId
     * @returns DeactivationResponse
     * @throws ApiError
     */
    public static v1UnitsDeactivateCreate(
        resourceId: string,
    ): CancelablePromise<DeactivationResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/units/{resource_id}/deactivate/',
            path: {
                'resource_id': resourceId,
            },
        });
    }
}
