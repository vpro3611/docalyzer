from enum import StrEnum 

class ModelEnum(StrEnum):
    LOW = "low"
    MID = "mid"
    HIGH = "high"

MODEL_MAP = {
    ModelEnum.LOW: "gemini-2.5-flash-lite",
    ModelEnum.MID: "gemini-2.5-flash",
    ModelEnum.HIGH: "gemini-2.5-pro",
}