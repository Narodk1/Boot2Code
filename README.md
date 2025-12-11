# Sonalyse Advisor

Sonalyse Advisor is an advanced acoustic diagnostic tool designed to analyze sound data from residential environments and provide actionable insights to improve acoustic comfort. This project leverages Python, Streamlit, and AI-based models to generate detailed reports and recommendations.

## Features

- **Acoustic Analysis**: Processes sound data to calculate average, minimum, maximum, and peak decibel levels.
- **Noise Source Identification**: Identifies dominant noise sources and their hourly/daily distribution.
- **Recommendations**: Provides tailored solutions to improve acoustic comfort, categorized into low-cost, intermediate, and heavy investments.
- **Interactive Visualizations**: Displays data insights using Streamlit and D3.js.
- **PDF Report Generation**: Generates comprehensive acoustic diagnostic reports.

## Project Structure

```
sonalyse_advisor/
├── agent_backend.py       # Backend logic for AI-based analysis
├── config.py              # Configuration file for model settings
├── context.txt            # Context file for AI prompts
├── dps_analysis_pi3_exemple.json  # Example JSON data for analysis
├── json_utils.py          # Utility functions for JSON data processing
├── main.py                # Entry point for the application
├── __pycache__/           # Cached Python files
.env                       # Environment variables (e.g., API keys)
app.py                     # Streamlit app for the user interface
```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Narodk1/Boot2Code.git
   cd Boot2Code
   ```

2. Set up a virtual environment:
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Create a `.env` file in the root directory.
   - Add your API key for the Groq model:
     ```
     GROQ_API_KEY=your_api_key_here
     ```

## Usage

1. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```

2. Upload your JSON data file for analysis.
3. View the results, including noise metrics, visualizations, and recommendations.
4. Generate a PDF report if needed.

## Example Data

The project includes an example JSON file (`dps_analysis_pi3_exemple.json`) to demonstrate the analysis process. Replace this file with your own data for custom diagnostics.

## Contributing

Contributions are welcome! If you'd like to improve this project, please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Acknowledgments

- **Groq API**: For powering the AI-based analysis.
- **Streamlit**: For creating an interactive and user-friendly interface.
- **D3.js**: For advanced data visualizations.

---

For any questions or support, please contact the project maintainer.