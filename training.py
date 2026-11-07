from src.network import network, input_data
import torch
import torch.nn as nn

import random
import datetime
import math

import numpy as np

from torch.utils.data import TensorDataset, DataLoader, random_split

# ==========================================
# CONFIGURATION
# ==========================================

NUM_SAMPLES = 20_000
MAX_PEOPLE = 300

BATCH_SIZE = 64
TRAIN_SPLIT = 0.8

RANDOM_SEED = 42

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
torch.manual_seed(RANDOM_SEED)


WEATHER_TYPES = ["Sunny", "Overcast", "Raining"]


# ==========================================
# OCCUPANCY SIMULATION
# ==========================================
import matplotlib.pyplot as plt


def plot_results(results):

    actual = results["actual"]
    predicted = results["predicted"]
    errors = results["errors"]

    fig, axes = plt.subplots(1, 2, figsize=(15, 5))

    # ----------------------------------
    # Actual vs predicted
    # ----------------------------------

    axes[0].scatter(
        actual,
        predicted,
        alpha=0.4,
        color="royalblue"
    )

    axes[0].plot(
        [0, 300],
        [0, 300],
        color="red",
        linestyle="--",
        label="Perfect prediction"
    )

    axes[0].set_title("Actual vs Predicted People")
    axes[0].set_xlabel("Actual People")
    axes[0].set_ylabel("Predicted People")

    axes[0].set_xlim(0, 300)
    axes[0].set_ylim(0, 300)

    axes[0].legend()
    axes[0].grid(alpha=0.3)

    # ----------------------------------
    # Prediction error distribution
    # ----------------------------------

    axes[1].hist(
        errors,
        bins=30,
        color="orange",
        edgecolor="black"
    )

    axes[1].axvline(
        0,
        color="red",
        linestyle="--",
        label="Zero error"
    )

    axes[1].set_title("Prediction Error Distribution")
    axes[1].set_xlabel("Error (People)")
    axes[1].set_ylabel("Number of Predictions")

    axes[1].legend()
    axes[1].grid(alpha=0.3)

    plt.tight_layout()
    plt.show()

def evaluate_model(model, test_loader, max_people=300):

    model.eval()

    actual_values = []
    predicted_values = []

    with torch.no_grad():

        for inputs, targets in test_loader:

            predictions = model(inputs)

            # Convert normalized values back to people.
            actual = targets.squeeze(1) * max_people
            predicted = predictions.squeeze(1) * max_people

            actual_values.extend(actual.tolist())
            predicted_values.extend(predicted.tolist())

    actual_values = np.array(actual_values)
    predicted_values = np.array(predicted_values)

    errors = predicted_values - actual_values
    absolute_errors = np.abs(errors)

    # Calculate metrics.
    mae = np.mean(absolute_errors)
    rmse = np.sqrt(np.mean(errors ** 2))
    max_error = np.max(absolute_errors)
    accuracy_within_5 = np.mean(absolute_errors <= 5) * 100
    accuracy_within_10 = np.mean(absolute_errors <= 10) * 100

    print("\n" + "=" * 65)
    print("              LIBRARY OCCUPANCY MODEL RESULTS")
    print("=" * 65)

    print(f"Total test samples:       {len(actual_values)}")
    print(f"Mean absolute error:      {mae:.2f} people")
    print(f"Root mean squared error:  {rmse:.2f} people")
    print(f"Worst prediction error:  {max_error:.2f} people")

    print(f"Within 5 people:          {accuracy_within_5:.2f}%")
    print(f"Within 10 people:         {accuracy_within_10:.2f}%")

    print("=" * 65)

    # Show individual predictions.
    print("\nSAMPLE PREDICTIONS")
    print("-" * 65)

    print(
        f"{'Actual':>10} "
        f"{'Predicted':>12} "
        f"{'Error':>12} "
        f"{'Result':>15}"
    )

    print("-" * 65)

    for i in range(min(20, len(actual_values))):

        actual = actual_values[i]
        predicted = predicted_values[i]
        error = predicted - actual

        if abs(error) <= 5:
            result = "Excellent"
        elif abs(error) <= 10:
            result = "Good"
        elif abs(error) <= 20:
            result = "Fair"
        else:
            result = "Poor"

        print(
            f"{actual:>10.0f} "
            f"{predicted:>12.1f} "
            f"{error:>+12.1f} "
            f"{result:>15}"
        )

    print("-" * 65)

    # Show best prediction.
    best_index = np.argmin(absolute_errors)

    print("\nBEST PREDICTION")
    print(f"Actual:    {actual_values[best_index]:.0f} people")
    print(f"Predicted: {predicted_values[best_index]:.1f} people")
    print(f"Error:     {errors[best_index]:+.1f} people")

    # Show worst prediction.
    worst_index = np.argmax(absolute_errors)

    print("\nWORST PREDICTION")
    print(f"Actual:    {actual_values[worst_index]:.0f} people")
    print(f"Predicted: {predicted_values[worst_index]:.1f} people")
    print(f"Error:     {errors[worst_index]:+.1f} people")

    print("\n" + "=" * 65)

    return {
        "actual": actual_values,
        "predicted": predicted_values,
        "errors": errors,
        "mae": mae,
        "rmse": rmse,
    }

def generate_people(hour: int, weather: str) -> int:
    """
    Generate a realistic-ish library occupancy value.

    Occupancy depends on:
    - Time of day
    - Weather
    - Random variation
    """

    # Library occupancy throughout the day.
    #
    # Quiet in the morning
    # Busy around midday
    # Busy during the afternoon
    # Quieter in the evening

    hourly_occupancy = {
        0: 0.01,
        1: 0.01,
        2: 0.01,
        3: 0.01,
        4: 0.01,
        5: 0.02,
        6: 0.03,
        7: 0.08,
        8: 0.20,
        9: 0.40,
        10: 0.60,
        11: 0.75,
        12: 0.85,
        13: 0.90,
        14: 0.95,
        15: 0.90,
        16: 0.85,
        17: 0.75,
        18: 0.60,
        19: 0.45,
        20: 0.30,
        21: 0.15,
        22: 0.08,
        23: 0.03,
    }

    occupancy = hourly_occupancy[hour]

    # Weather influences library attendance.
    # For example, people may prefer studying indoors
    # when it is raining.

    weather_multiplier = {
        "Sunny": 0.90,
        "Overcast": 1.00,
        "Raining": 1.10,
    }

    occupancy *= weather_multiplier[weather]

    # Random variation so the data isn't deterministic.
    occupancy += np.random.normal(0, 0.12)

    occupancy = np.clip(occupancy, 0.0, 1.0)

    # Convert occupancy percentage into people.
    people = int(occupancy * MAX_PEOPLE)

    # Add some individual variation.
    people += random.randint(-10, 10)

    return max(0, min(MAX_PEOPLE, people))


# ==========================================
# BLUETOOTH SIMULATION
# ==========================================

def generate_bluetooth_connections(people: int) -> int:
    """
    Simulate the number of BLE devices detected.

    Not everyone has their Bluetooth enabled.
    Some people may have multiple devices.
    """

    # Average number of detected devices per person.
    detection_rate = 0.85

    # Most people have approximately one device,
    # but some have additional devices.
    expected_connections = people * detection_rate

    connections = np.random.poisson(expected_connections)

    # Occasionally generate additional connections
    # from devices that aren't associated with people.
    connections += np.random.poisson(2)

    return max(0, connections)


# ==========================================
# WEATHER SIMULATION
# ==========================================

def generate_weather() -> str:
    """
    Randomly generate weather conditions.

    The probabilities can be changed to suit
    your expected environment.
    """

    return random.choices(
        WEATHER_TYPES,
        weights=[0.35, 0.40, 0.25],
        k=1
    )[0]


# ==========================================
# TIME SIMULATION
# ==========================================

def generate_time() -> datetime.datetime:
    """
    Generate a random datetime.

    The neural network will primarily use the hour.
    """

    year = 2026
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)

    return datetime.datetime(
        year, month, day, hour, minute
    )


# ==========================================
# DATASET GENERATION
# ==========================================

def generate_dataset(num_samples: int):

    X = []
    y = []

    for _ in range(num_samples):

        # Generate environment.
        time = generate_time()
        weather = generate_weather()

        # Generate actual people count.
        people = generate_people(
            time.hour,
            weather
        )

        # Generate BLE connections.
        bluetooth_connections = generate_bluetooth_connections(
            people
        )

        # Build your input data object.
        input_instance = input_data.InputData(
            input_data.BluetoothData(
                bluetooth_connections
            ),
            input_data.WeatherData(
                value=weather
            ),
            input_data.TimeData(
                time=time
            )
        )

        # Convert to your existing input format.
        input_array = input_instance.create_input_array()

        X.append(input_array)

        # Normalize output to 0-1.
        normalized_people = people / MAX_PEOPLE

        y.append([normalized_people])

    # Convert to PyTorch tensors.
    X = torch.tensor(
        X,
        dtype=torch.float32
    )

    y = torch.tensor(
        y,
        dtype=torch.float32
    )

    return X, y


# ==========================================
# CREATE TRAINING DATA
# ==========================================

X, y = generate_dataset(NUM_SAMPLES)

print("Dataset generated!")
print("Input tensor shape:", X.shape)
print("Output tensor shape:", y.shape)

print("\nExample input:")
print(X[0])

print("\nExample output:")
print(y[0])



dataset = TensorDataset(X, y)

train_size = int(len(dataset) * TRAIN_SPLIT)
test_size = len(dataset) - train_size

train_dataset, test_dataset = random_split(
    dataset,
    [train_size, test_size]
)

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True
)

test_loader = DataLoader(
    test_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False
)


# Create

model = network.InternalNeuralNetwork()

criterion = nn.MSELoss()

optimizer = torch.optim.Adam(
    model.parameters(),
    lr=0.001
)

EPOCHS = 1000

for epoch in range(EPOCHS):

    model.train()

    total_loss = 0

    for inputs, targets in train_loader:

        predictions = model(inputs)  # NOQA - It sure is callable pycharm!

        loss = criterion(predictions, targets)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    average_loss = total_loss / len(train_loader)

    if (epoch + 1) % 10 == 0:
        print(
            f"Epoch {epoch + 1}/{EPOCHS} "
            f"Loss: {average_loss:.6f}"
        )

results = evaluate_model(model, test_loader)  # NOQA - The model does have those attrs pycharm
plot_results(results)

torch.save(model.state_dict(), "locations/Library2.net")
