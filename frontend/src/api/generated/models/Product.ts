/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ProductAttributeValue } from './ProductAttributeValue';
import type { ProductPrice } from './ProductPrice';
import type { ProductSpecificationValue } from './ProductSpecificationValue';
export type Product = {
    readonly id: string;
    name: string;
    unit_id: string;
    unit_name: string;
    supplier_id: string | null;
    supplier_name: string | null;
    purchase_price?: string;
    specification?: string;
    remark?: string;
    is_active?: boolean;
    readonly specification_values: Array<ProductSpecificationValue>;
    readonly attribute_values: Array<ProductAttributeValue>;
    readonly prices: Array<ProductPrice>;
    stock_quantity: string;
    readonly created_at: string;
    readonly updated_at: string;
};

