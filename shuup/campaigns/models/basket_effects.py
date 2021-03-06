# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from django.db import models
from django.utils.translation import ugettext_lazy as _

from shuup.admin.forms.fields import PercentageField
from shuup.core.fields import MoneyValueField
from shuup.core.models import PolymorphicShuupModel
from shuup.core.pricing import PricingContext


class BasketDiscountEffect(PolymorphicShuupModel):
    identifier = None
    model = None
    admin_form_class = None

    campaign = models.ForeignKey("BasketCampaign", related_name="discount_effects", verbose_name=_("campaign"))

    def apply_for_basket(self, order_source):
        """
        Applies the effect based on given `order_source`

        :return: amount of discount to accumulate for the product
        :rtype: Price
        """
        raise NotImplementedError("Not implemented!")


class BasketDiscountAmount(BasketDiscountEffect):
    identifier = "discount_amount_effect"
    name = _("Discount amount value")

    discount_amount = MoneyValueField(
        default=None, blank=True, null=True,
        verbose_name=_("discount amount"),
        help_text=_("Flat amount of discount."))

    @property
    def description(self):
        return _("Give discount amount.")

    @property
    def value(self):
        return self.discount_amount

    @value.setter
    def value(self, value):
        self.discount_amount = value

    def apply_for_basket(self, order_source):
        return order_source.create_price(self.value)


class BasketDiscountPercentage(BasketDiscountEffect):
    identifier = "discount_percentage_effect"
    name = _("Discount amount percentage")
    admin_form_class = PercentageField

    discount_percentage = models.DecimalField(
        max_digits=6, decimal_places=5, blank=True, null=True,
        verbose_name=_("discount percentage"),
        help_text=_("The discount percentage for this campaign."))

    @property
    def description(self):
        return _("Give percentage discount.")

    @property
    def value(self):
        return self.discount_percentage

    @value.setter
    def value(self, value):
        self.discount_percentage = value

    def apply_for_basket(self, order_source):
        return (order_source.total_price_of_products * self.value)


class DiscountPercentageFromUndiscounted(BasketDiscountEffect):
    identifier = "undiscounted_percentage_effect"
    name = _("Discount amount percentage from undiscounted amount")
    admin_form_class = PercentageField

    discount_percentage = models.DecimalField(
        max_digits=6, decimal_places=5, blank=True, null=True,
        verbose_name=_("discount percentage"),
        help_text=_("The discount percentage for this campaign."))

    @property
    def description(self):
        return _("Give percentage discount based on undiscounted product prices.")

    @property
    def value(self):
        return self.discount_percentage

    @value.setter
    def value(self, value):
        self.discount_percentage = value

    def apply_for_basket(self, order_source):
        from shuup.campaigns.models import CatalogCampaign
        discounted_base_amount = order_source.total_price_of_products
        context = PricingContext(order_source.shop, order_source.customer)
        for line in order_source.get_product_lines():
            product = line.product
            if CatalogCampaign.get_matching(context, product.get_shop_instance(order_source.shop)):
                discounted_base_amount -= line.price
        return (discounted_base_amount * self.value)
