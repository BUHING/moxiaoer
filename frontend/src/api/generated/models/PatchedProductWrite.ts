/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ProductAttributeValueInput } from './ProductAttributeValueInput';
import type { ProductPriceInput } from './ProductPriceInput';
import type { ProductSpecificationValueInput } from './ProductSpecificationValueInput';
export type PatchedProductWrite = {
    name?: string;
    unit_id?: string;
    supplier_id?: string | null;
    purchase_price?: string;
    specification?: string;
    remark?: string;
    is_active?: boolean;
    specification_values?: Array<ProductSpecificationValueInput>;
    attribute_values?: Array<ProductAttributeValueInput>;
    prices?: Array<ProductPriceInput>;
    initial_quantity?: string;
};

