from datetime import datetime
from typing import Literal, get_args

weathers = Literal["Sunny", "Overcast", "Raining"]

class WeatherData:
    def __init__(self, value: weathers | None = None):
        if value is None:
            value = self.get_current_weather_at_location()

        self.weather = value

        if self.weather not in get_args(weathers):
            raise ValueError(f"Invalid weather: {self.weather} not in {get_args(weathers)}")

    def get_current_weather_at_location(self) -> weathers:
        raise NotImplementedError("Weather forcast fetching not implemented")

    def get_weather_values(self) -> list[int]:
        options = get_args(weathers)
        current = options.index(self.weather)

        return [
            1 if current == i else 0
            for i in range(len(options))
        ]

class TimeData:
    def __init__(self, time: datetime | None = None):
        if time is None:
            time = datetime.now()

        self.time = time

    def get_hour(self) -> list[int]:
        data_hour = self.time.hour

        return [
            1 if hour == data_hour else 0
            for hour in range(7, 20)  # 0 -> 23
        ]

class BluetoothData:
    head_count: int
    def __init__(self, head_count: int):
        self.head_count = head_count

    def get_head_count(self) -> int:
        return self.head_count


class InputData:
    weather: WeatherData
    time: TimeData
    devices: BluetoothData

    def __init__(self, bluetooth_data: BluetoothData, weather_data: WeatherData, time_data: TimeData, normal_capacity: int = 300):
        self.weather = weather_data
        self.time = time_data
        self.devices = bluetooth_data
        self.normal_capacity = normal_capacity


    def create_input_array(self) -> list[int | float]:
        return [
            *self.weather.get_weather_values(),
            *self.time.get_hour(),
            self.devices.get_head_count() / self.normal_capacity,
        ]
