Example output for USA:
![us datacentres first pass](https://github.com/user-attachments/assets/49003939-ed1e-4a3f-a0f3-689d65fa7048)
Example aggregate of all economy's with confidence intervals. (note the bottom half of the total's conf int. is covered by the data centres conf. int.):
![aggregate with confidence intervals first pass](https://github.com/user-attachments/assets/a2f22d95-783a-4102-9375-e790d0aeb883)


# General structure:
The code is based around the main.py function, except in the case of estimate_inputs.py - which is better to be run as it's own independent script.

## estimate_inputs.py and parameters.yml
The outputs are dictated by what is in the config/parameters.yml file. These can be edited en-masse using the estimate_inputs.py script, or manually edited where you need specific edits. Chances are that as you complete the model for each economy, you will want to remove them from the estiamte_inputs.py process using the ECONOMIES_TO_KEEP_AS_IS list variable. Also the script will save a dated copy of the previous parameters file to config/previous_parameter_versions/parameters_{date_id}.yml just in case you screw something up. This is pretty useful for testing things.

## main.py and projection_functions.py
This is where the magic happens. Main.py will run project_energy_use() which will produce a projectino for each economy in parameters.yml. Then after that everything is to do with creating charts and comparisons to data from the buildings model and previous 8th/9th outlook projections. Below I've written (or chatgpt has written) a guide to project energy use. I think reading the code at the same time is most useful.

# 📄 Documentation for `project_energy_use(config)`

Hope you enjoy my chatgpt generated (and slightly adjusted manually) doucmentation with emojis.

## 🎯 Purpose

The `project_energy_use` function 📊 projects the energy ⚡ consumption for data 📈 activity and AI 🤖 training activity over a specified 🗓️ time period for one or more 🌍 economies. It allows users 👥 to model how different growth 📈 rates, intensity 🔧 improvements, and scheduled 📅 infrastructure 🏗️ builds affect overall energy ⚡ use.

## 📝 Function Signature

```python
def project_energy_use(config):
```

## 📥 Parameters

- **`config`** (`dict`): A configuration 📋 dictionary containing:
  - **`start_year`** (`int`): The starting year 🗓️ for the projection.
  - **`end_year`** (`int`): The ending year 🗓️ for the projection.
  - **`economies`** (`list` of `dict`): A list 📜 of economies 🌍 to model, each with their own parameters.

## 🌍 Economy Configuration

Each economy dictionary within `config['economies']` should include:

- **`name`** (`str`): Name 🏷️ of the economy.
- **`initial_data_activity_growth_rate`** (`float`): Initial growth rate 📈 for data activity (e.g., `0.15` for 15%).
- **`initial_ai_training_activity_growth_rate`** (`float`): Initial growth rate 📈 for AI 🤖 training activity.
- **`initial_data_intensity_improvement_rate`** (`float`): Initial rate 📉 of improvement in data intensity.
- **`initial_ai_training_intensity_improvement_rate`** (`float`): Initial rate 📉 of improvement in AI 🤖 training intensity.
- **`initial_data_to_ai_training_ratio`** (`float`): Initial ratio ⚖️ of data activity to AI 🤖 training activity energy use (value between `0` and `1`).

### 🔋 Initial Energy

Specify one of the following to indicate initial energy ⚡ consumption:

- **`initial_energy_pj`** (`float`): Initial energy in petajoules (PJ).
- **`initial_energy_mw`** (`float`): Initial energy capacity in megawatts (MW).
- **`initial_energy_mwh`** (`float`): Initial energy in megawatt-hours (MWh).
- **`initial_energy_twh`** (`float`): Initial energy in terawatt-hours (TWh).

### 🔧 Optional Parameters

- **`scheduled_builds`** (`list` of `dict`): Scheduled 🗓️ infrastructure 🏗️ additions with parameters:
  - **`year`** (`int`): Year 🗓️ of the scheduled build.
  - **🔋 Additional Energy**: Specify one of the following:
    - **`additional_energy_pj`** (`float`)
    - **`additional_energy_mw`** (`float`)
    - **`additional_energy_mwh`** (`float`)
    - **`additional_energy_twh`** (`float`)
  - **`new_data_to_ai_training_ratio`** (`float`, optional): New ratio ⚖️ applied to this years build and onwards.
- **`new_activity_growth_rates`** (`list` of `dict`): Changes 🔄 in growth rates:
  - **`year`** (`int`): Year 🗓️ the new growth rates take effect.
  - **`new_data_growth_rate`** (`float`): New data 📊 activity growth rate.
  - **`new_ai_growth_rate`** (`float`): New AI 🤖 training activity growth rate.
- **`new_intensity_improvement_rates`** (`list` of `dict`): Changes 🔄 in intensity improvement rates:
  - **`year`** (`int`): Year 🗓️ the new rates take effect.
  - **`new_data_intensity_improvement_rate`** (`float`): New data 📊 intensity improvement rate.
  - **`new_ai_training_intensity_improvement_rate`** (`float`): New AI 🤖 training intensity improvement rate.

## 📤 Returns

- **`combined_projections`** (`pandas.DataFrame`): A DataFrame 📊 containing projected energy use data for all economies 🌍 over the specified time period 🗓️.

## 🔍 How It Works

### 🛠️ Initialization

1. **Extract Configuration**:
   - Retrieves `start_year`, `end_year`, and iterates 🔄 over each economy in `config['economies']`.
   - Initializes an empty list 📋 `all_projections` to store projections for each economy 🌍.

### ⚙️ Processing Each Economy

1. **Extract Parameters**:
   - Retrieves initial growth 📈 rates, intensity 🔧 improvement rates, and the data-to-AI 🤖 training ratio ⚖️.
   - Calculates `initial_energy_pj` based on the specified initial energy (converts units if necessary).

2. **Set Up DataFrame**:
   - Creates a DataFrame `df` 📊 with years from `start_year` to `end_year`.
   - Initializes columns for growth rates 📈, intensity rates 🔧, activities 📊, intensities 🔧, and ratios ⚖️.

3. **Apply New Rates**:
   - Updates growth rates 📈 and intensity improvement rates 🔧 in `df` based on `new_activity_growth_rates` and `new_intensity_improvement_rates`.

4. **Initial Calculations**:
   - Calculates initial activities 📊 and intensities 🔧 for data and AI 🤖 training based on the initial energy ⚡ and ratio ⚖️.

### 🔄 Projection Loop

For each subsequent year 🗓️:

1. **Update Intensities**:
   - Applies intensity improvements 🔧 based on the improvement rates.

2. **Scheduled Builds**:
   - Checks if there is a scheduled build 🏗️ for the current year 🗓️.
     - **If found**:
       - Adjusts activities 📊 based on additional energy ⚡ and applies them according to any new ratios ⚖️ (if no new ratios, will use the last one available)
     - **If not**:
       - Grows activities 📊 based on growth rates 📈.

3. **Calculate Energy Use**:
   - Calculates energy ⚡ use for data 📊 and AI 🤖 training activities using the newly projected activity and intensity.

4. **Index Activities**:
   - Normalizes activities 📊 to the base year 🗓️ for comparative analysis 📈.

### 📦 Collect Projections

- Appends the DataFrame `df` 📊 for the current economy 🌍 to `all_projections` 📋.

### 📊 Combining Results

- Concatenates all individual economy projections 📊 into `combined_projections`.

---

By following these steps 📝, the function provides a detailed projection 📊 of energy use ⚡, considering various factors like growth rates 📈, intensity improvements 🔧, and scheduled builds 🏗️, allowing for comprehensive energy planning and analysis 🔍.

# some clarifications:

- **`data_to_ai_training_ratio`** (`float`): Ratio ⚖️ of data activity to AI 🤖 training activity for scheduled builds only. To make it work with the rest of the process, the energy is converted to activity using the intensity value and then back again using the intensity value. So it doesn't matter what the intensity value is for these scheduled build years, but it is really important what the data_to_ai_training_ratio is. Also, the activity growth rates don't matter for these scheduled build years because the change in activity in that year is determined by the scheduled build, if there is one.
