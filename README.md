# IP Geolocation Using Traceroute Location Propagation and IP Range Location Interpolation

A Python implementation of the paper "IP Geolocation Using Traceroute Location Propagation and IP Range Location Interpolation" (WWW 2021).

## Overview

This project implements a novel IP geolocation technique that combines two key methods:

1. **Traceroute Location Propagation**: Propagates IP location information through traceroute paths by leveraging latency relationships between network hops
2. **IP Range Location Interpolation**: Expands location coverage by inferring locations for entire IP ranges based on known IPs within those ranges

The approach significantly outperforms commercial geolocation databases by up to 31 percentage points in accuracy.

## Key Features

- ✅ **Latency Neighbor Extraction**: Identifies IP pairs with similar network latency
- ✅ **Neighbor Pair Aggregation**: Aggregates the same IP pair across multiple traceroutes
- ✅ **IP Range Interpolation**: Expands ground truth coverage using /24 network segments
- ✅ **Iterative Location Propagation**: Propagates locations through the network graph
- ✅ **Flexible Configuration**: Support for both high-accuracy and high-coverage modes

## Project Structure

```
.
├── src/
│   ├── data_processing/           # Data loading and parsing
│   │   ├── traceroute_parser.py   # Parse traceroute data
│   │   └── ground_truth_loader.py # Load ground truth locations
│   ├── latency_neighbors/         # Latency neighbor extraction
│   │   └── neighbor_extractor.py  # Extract and aggregate neighbor pairs
│   ├── ip_range_interpolation/    # IP range interpolation
│   │   └── range_interpolator.py  # Interpolate locations for IP ranges
│   ├── location_propagation/      # Location propagation
│   │   └── propagator.py          # Propagate locations through network
│   └── utils/
│       ├── config_loader.py       # Load configuration
│       └── geo_utils.py           # Geographic utilities
├── config/
│   └── config.yaml                # Configuration file
├── data/
│   ├── ground_truth/              # Ground truth IP locations
│   ├── traceroute/                # Traceroute data
│   └── output/                    # Output results
├── main.py                        # Main entry point
└── requirements.txt               # Python dependencies
```

## Installation

### Prerequisites
- Python 3.7+
- pip

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/IP-Geo.git
cd IP-Geo

# Install dependencies
pip install -r requirements.txt
```

## Usage

### 1. Prepare Data

Place your data in the following structure:

```
data/
├── ground_truth/
│   └── ground_truth.csv          # Format: ip,latitude,longitude
└── traceroute/
    └── traceroute_sample.txt     # Format: source_ip dest_ip hop1 rtt1 hop2 rtt2 ...
```

### 2. Configure Parameters

Edit `config/config.yaml` to adjust parameters:

```yaml
latency_neighbors:
  high_accuracy:
    max_latency_diff: 2    # X: Maximum latency difference (ms)
    max_rtt: 2             # Y: Maximum RTT (ms)
  high_coverage:
    max_latency_diff: 3
    max_rtt: 9

ip_range_interpolation:
  range_size: 256          # /24 network segment
  min_ground_truth: 2      # n: Minimum known IPs per range
  max_distance_km: 25      # m: Maximum distance within range (km)

location_propagation:
  mode: "high_accuracy"    # or "high_coverage"
  max_iterations: 10
  convergence_threshold: 0.01
```

### 3. Run the Pipeline

```bash
python main.py
```

### Output

Results are saved to `data/output/`:

- `latency_neighbors_high_accuracy.csv`: Extracted neighbor pairs (high accuracy)
- `latency_neighbors_high_coverage.csv`: Extracted neighbor pairs (high coverage)
- `ip_ranges.csv`: Valid IP ranges with center coordinates
- `interpolated_ips.csv`: IPs with interpolated locations
- `propagated_ips.csv`: IPs with propagated locations
- `all_locations.csv`: Complete results (interpolated + propagated)

## Method Details

### Step 1: Latency Neighbor Extraction

Identifies IP pairs that are close in network latency:

```
Condition: |RTT(ip1) - RTT(ip2)| ≤ X ms AND RTT(ip1), RTT(ip2) ≤ Y ms
```

**Two-stage aggregation**:
1. Aggregate RTT for each (source_ip, hop_ip) pair across multiple traceroutes
2. Aggregate latency differences for the same IP pair across traceroutes

### Step 2: IP Range Interpolation

Expands location coverage by assigning locations to entire /24 network segments:

```
For each /24 range:
  IF (number of known IPs ≥ n) AND (all IPs within m km):
    THEN assign centroid location to entire range
```

**Parameters**:
- n = 2 (minimum known IPs)
- m = 25 km (maximum distance)

**Result**: Expands coverage from 890M to 3.82B IPs in the paper

### Step 3: Location Propagation

Iteratively propagates locations through the network graph:

```
Iteration 1: Propagate to IPs 1-hop away from known IPs
Iteration 2: Propagate to IPs 2-hops away
...
Until convergence or max iterations reached
```

**Location calculation**: Average of neighbor locations

## Configuration Modes

### High Accuracy Mode
- Parameters: X=2ms, Y=2ms
- Median error: ~4.3 km
- Accuracy (<10km): ~67.7%
- Best for: Fraud detection, content licensing

### High Coverage Mode
- Parameters: X=3ms, Y=9ms
- Median error: ~10.1 km
- Accuracy (<10km): ~50.5%
- Best for: Ad targeting, content personalization

## Paper Reference

**Title**: IP Geolocation Using Traceroute Location Propagation and IP Range Location Interpolation

**Authors**: Ovidiu Dan, Vaibhav Parikh, Brian D. Davison

**Conference**: WWW 2021 (The Web Conference 2021)

**DOI**: 10.1145/3442442.3451888

**Link**: https://dl.acm.org/doi/10.1145/3442442.3451888

## Key Results

| Metric | High Accuracy | High Coverage | Commercial DB A | Commercial DB B |
|--------|---------------|---------------|-----------------|-----------------|
| Median Error | 4.3 km | 10.1 km | 11.1 km | 16.7 km |
| <10km Accuracy | 67.7% | 50.5% | 47.2% | 36.7% |
| <20km Accuracy | 99.4% | 98.3% | - | - |

## Implementation Notes

### Data Format

**Ground Truth CSV**:
```csv
ip,latitude,longitude
8.8.8.8,37.386,-122.084
1.1.1.1,37.751,-97.822
```

**Traceroute TXT**:
```
source_ip dest_ip hop1 rtt1 hop2 rtt2 hop3 rtt3 ...
100.38.192.94 129.11.202.144 107.15.57.240 2.04 22.55.246.62 3.40 ...
```

### Key Algorithms

1. **Haversine Distance**: Calculate great-circle distance between coordinates
2. **Centroid Calculation**: Compute center point of multiple locations
3. **Iterative Propagation**: Graph-based location spreading with convergence detection

## Dependencies

- numpy: Numerical computations
- pandas: Data manipulation
- pyyaml: Configuration parsing

See `requirements.txt` for specific versions.

## Limitations

- Requires sufficient ground truth data for accurate interpolation
- Depends on traceroute data quality and coverage
- Network topology changes may affect accuracy
- Privacy considerations for location data

## Future Improvements

- Support for IPv6 addresses
- Integration with reverse DNS information
- Machine learning-based location refinement
- Real-time location updates

## License

This project is provided for research and educational purposes.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## Citation

If you use this implementation in your research, please cite the original paper:

```bibtex
@inproceedings{dan2021ip,
  title={IP Geolocation Using Traceroute Location Propagation and IP Range Location Interpolation},
  author={Dan, Ovidiu and Parikh, Vaibhav and Davison, Brian D},
  booktitle={Companion Proceedings of the Web Conference 2021},
  pages={332--338},
  year={2021},
  organization={ACM}
}
```

## Contact

For questions or issues, please open an issue on GitHub.

---

**Last Updated**: 2026-03-11
