from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, model_validator
from sqlmodel import JSON, Column, Field, SQLModel


# --- Base Configurations ---
class BaseConfig(BaseModel):
    type: str = Field(..., description="The type of the component.")


# --- Source Configurations ---
class HTTPSourceConfig(BaseConfig):
    type: Literal["http"] = "http"
    path: str = Field(..., description="The HTTP path to listen on.")
    method: Literal["GET", "POST", "PUT", "DELETE"] = Field(
        ..., description="The HTTP method to accept."
    )


class TCPSourceConfig(BaseConfig):
    type: Literal["tcp"] = "tcp"
    port: int = Field(..., description="The TCP port to listen on.")
    host: str = Field("0.0.0.0", description="The host to bind to.")
    use_mllp: bool = Field(
        False, description="Whether to use MLLP framing for HL7 messages."
    )


# Use a Union for SourceConfig to allow different source types
# This will be stored as JSON in the database
SourceConfigType = Union[HTTPSourceConfig, TCPSourceConfig]


# --- Filter Configurations ---
class PythonScriptFilterConfig(BaseConfig):
    type: Literal["python_script"] = "python_script"
    script: str = Field(
        ...,
        description="Python script for filtering messages. Must return True to pass, False to filter out.",
    )


# Use a Union for FilterConfig to allow different filter types
# This will be stored as JSON in the database
FilterConfigType = Union[PythonScriptFilterConfig]


# --- Transformer Configurations ---
class PythonScriptTransformerConfig(BaseConfig):
    type: Literal["python_script"] = "python_script"
    script: str = Field(
        ...,
        description="Python script for transforming messages. Must return the transformed message.",
    )


# Use a Union for TransformerConfig to allow different transformer types
# This will be stored as JSON in the database
TransformerConfigType = Union[PythonScriptTransformerConfig]


# --- Destination Configurations ---
class HTTPDestinationConfig(BaseConfig):
    type: Literal["http"] = "http"
    url: str = Field(..., description="The URL to send the message to.")
    method: Literal["GET", "POST", "PUT", "DELETE"] = Field(
        "POST", description="The HTTP method to use."
    )
    headers: Optional[Dict[str, str]] = Field(
        None, description="Optional HTTP headers."
    )


class TCPDestinationConfig(BaseConfig):
    type: Literal["tcp"] = "tcp"
    host: str = Field(..., description="The TCP host to connect to.")
    port: int = Field(..., description="The TCP port to connect to.")
    use_mllp: bool = Field(
        False, description="Whether to use MLLP framing for HL7 messages."
    )


# Use a Union for DestinationConfig to allow different destination types
# This will be stored as JSON in the database
DestinationConfigType = Union[HTTPDestinationConfig, TCPDestinationConfig]


# --- Channel Model (SQLModel) ---
class ChannelModel(SQLModel, table=True):
    id: Optional[str] = Field(
        default=None, primary_key=True, description="Unique identifier for the channel."
    )
    name: str = Field(
        ..., index=True, description="Human-readable name for the channel."
    )
    description: Optional[str] = Field(
        None, description="Optional description of the channel."
    )
    enabled: bool = Field(default=True, description="Whether the channel is active.")

    # Store configurations as JSON
    source: SourceConfigType = Field(
        sa_column=Column(JSON), description="Configuration for the data source."
    )
    filters: Optional[List[FilterConfigType]] = Field(
        default=None, sa_column=Column(JSON), description="List of message filters."
    )
    transformers: Optional[List[TransformerConfigType]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="List of message transformers.",
    )
    destinations: List[DestinationConfigType] = Field(
        sa_column=Column(JSON), description="List of data destinations."
    )

    
