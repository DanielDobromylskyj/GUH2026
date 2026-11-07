from datetime import datetime
from typing import Literal, get_args
import asyncio
import python_weather
from datetime import datetime

weathers = Literal["Sunny", "Overcast", "Raining"]


class WeatherData:
    def __init__(self, value: str | weathers | None = None):
        self.weather: weathers | None = None

        if value is None:
            return

        if value in get_args(weathers):
            self.weather = value
        else:
            self.weather = asyncio.run(
                self.get_current_weather_at_location(value)
            )

    @staticmethod
    async def get_current_weather_at_location(location: str) -> weathers:
        async with python_weather.Client(
            unit=python_weather.METRIC
        ) as weather_client:

            weather = await weather_client.get(location)

            forecast_chunk = datetime.now().hour // 3
            weather_code = (
                weather.daily_forecasts[0]
                .hourly_forecasts[forecast_chunk]
                .kind.value
            )

            if weather_code < 119:
                return "Sunny"
            elif weather_code <= 176:
                return "Overcast"
            else:
                return "Raining"

    def get_weather_values(self) -> list[int]:
        options = get_args(weathers)

        if self.weather is None:
            return [0] * len(options)

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
