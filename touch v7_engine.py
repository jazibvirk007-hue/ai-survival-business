from order_manager import (
    create_order,
    update_order,
    get_order
)

from payment_tracker import (
    create_payment_request,
    verified_revenue
)

from delivery_engine import (
    create_delivery
)


def create_customer_order(
    customer,
    business_name,
    product_name,
    price
):

    order = create_order(
        customer=customer,
        product=product_name,
        amount=price
    )

    payment = create_payment_request(
        order_id=order["order_id"],
        amount=price
    )

    return order, payment


def mark_payment_verified(
    order_id,
    transaction_id
):

    from payment_tracker import verify_payment

    success = verify_payment(
        order_id,
        transaction_id
    )

    if not success:
        return False

    update_order(
        order_id,
        payment_status="paid",
        status="paid"
    )

    return True


def deliver_order(
    order_id,
    customer,
    business_name,
    product_name
):

    order = get_order(order_id)

    if not order:
        return None

    if order["payment_status"] != "paid":
        print(
            "Delivery blocked: payment "
            "has not been verified."
        )

        return None

    filepath = create_delivery(
        order_id=order_id,
        customer=customer,
        product_name=product_name,
        business_name=business_name
    )

    update_order(
        order_id,
        status="delivered",
        delivery_status="delivered",
        delivery_file=filepath
    )

    return filepath