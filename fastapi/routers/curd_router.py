# Copyright 2023 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).
"""
The curd router is a router that demonstrates how to use the fastapi
integration with odoo.
"""
import json
from typing import Annotated

from odoo.api import Environment
from odoo.exceptions import AccessError, MissingError, UserError, ValidationError

from odoo.addons.base.models.res_partner import Partner

from fastapi import APIRouter, Depends, HTTPException, status

from odoo.models import BaseModel
from ..dependencies import authenticated_partner, fastapi_endpoint, odoo_env
from ..models import FastapiEndpoint
from ..schemas import DemoEndpointAppInfo, DemoExceptionType, DemoUserInfo
from odoo.http import request

router = APIRouter(tags=["curd"])


@router.get("/demo")
async def hello_word():
    """Hello World!"""
    return {"Hello": "World"}


@router.get("/partners")
def get_partners():
    partner = request.env['res.partner'].search([])
    return [{'name': rec.name, 'display_name': rec.display_name} for rec in partner]
