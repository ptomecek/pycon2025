""" 
Code for the PyCon 2025 talk "Dependency Injection in Python with Hydra" 
    $pip install hydra-core pydantic
    $python my_app.py +weather_api=test
"""

from typing import Annotated, Any
from pydantic import BaseModel, BeforeValidator

import hydra
import my_app


REGISTRY: dict[str, Any] = {}


def registry_lookup(value: Any) -> Any:
    if isinstance(value, str) and value in REGISTRY:
        return REGISTRY[value]
    return value


Injectable = BeforeValidator(registry_lookup)


class WeatherAPI(BaseModel, validate_assignment=True):
    def get_current_weather(self, city: str):
        ...


class OpenWeatherMapClient(WeatherAPI):
    api_key: str

    def get_current_weather(self, city: str):
        raise NotImplementedError


class MockWeatherAPI(WeatherAPI):
    temp: float
    conditions: str

    def get_current_weather(self, city: str):
        return dict(temp=self.temp, conditions=self.conditions)


class WeatherReportGenerator(BaseModel, validate_assignment=True):
    weather_api: Annotated[WeatherAPI, Injectable]

    def create_daily_report(self, city: str):
        weather_data = self.weather_api.get_current_weather(city)
        return (f"Weather in {city}: {weather_data['temp']}°C, "
            f"{weather_data['conditions']}")


# def populate_registry(cfg):
#     for k, v in cfg.items():
#         my_app.REGISTRY[k] = hydra.utils.instantiate(v)
#     return my_app.REGISTRY


# Order-independent version
def populate_registry(cfg):
    to_register = cfg.items()
    while True:
        unresolved = []
        for k, v in to_register:
            try:
                my_app.REGISTRY[k] = hydra.utils.instantiate(v)
            except Exception as e:
                unresolved.append((k, v))
        if not unresolved:
            break
        elif len(unresolved) == len(to_register):
            break
        else:
            to_register = unresolved
    return my_app.REGISTRY


@hydra.main(config_path="conf", config_name="config", version_base=None)
def run(cfg):
    # print(cfg)
    # print(hydra.utils.instantiate(cfg))
    registry = populate_registry(cfg)
    # Check that the instances are the same
    assert registry["weather_api"] is registry["report_generator"].weather_api
    # Call that app’s functionality, without knowledge of how it was constructed
    report = registry["report_generator"].create_daily_report("Pittsburgh")
    print(report)


if __name__ == "__main__":
    run()

