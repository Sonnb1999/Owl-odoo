# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import warnings
from enum import Enum
from typing import Annotated, Generic, List, Optional, TypeVar

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, computed_field, EmailStr
T = TypeVar("T")


class PagedCollection(BaseModel, Generic[T]):
    count: Annotated[
        int,
        Field(
            ...,
            description="Count of items into the system.\n "
            "Replaces the total field which is deprecated",
            validation_alias=AliasChoices("count", "total"),
        ),
    ]
    items: List[T]

    @computed_field()
    @property
    def total(self) -> int:
        return self.count

    @total.setter
    def total(self, value: int):
        warnings.warn(
            "The total field is deprecated, please use count instead",
            DeprecationWarning,
            stacklevel=2,
        )
        self.count = value


class Paging(BaseModel):
    limit: Optional[int] = None
    offset: Optional[int] = None


#############################################################
# here above you can find models only used for the demo app #
#############################################################
class DemoUserInfo(BaseModel):
    name: str
    display_name: str


class DemoEndpointAppInfo(BaseModel):
    id: int
    name: str
    app: str
    auth_method: str = Field(alias="demo_auth_method")
    root_path: str
    model_config = ConfigDict(from_attributes=True)


class DemoExceptionType(str, Enum):
    user_error = "UserError"
    validation_error = "ValidationError"
    access_error = "AccessError"
    missing_error = "MissingError"
    http_exception = "HTTPException"
    bare_exception = "BareException"


class User(BaseModel):
    username: str = None
    email: str


class ResponseMessage(BaseModel):
    message: str


class BackLink(BaseModel):
    link_tracker: str
    odoo_utm_params: dict
    referrer: str = None
    code: str = None


class PartnerData(BaseModel):
    name: str
    phone: str
