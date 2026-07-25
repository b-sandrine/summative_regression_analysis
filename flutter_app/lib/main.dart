import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

void main() {
  runApp(const CropYieldApp());
}

class ApiConfig {
  static String get baseUrl {
    const envUrl = String.fromEnvironment('API_BASE_URL', defaultValue: '');
    if (envUrl.isNotEmpty) {
      return envUrl;
    }

    if (kIsWeb) {
      return 'http://localhost:8000';
    }

    if (Platform.isAndroid) {
      return 'http://10.0.2.2:8000';
    }

    return 'http://127.0.0.1:8000';
  }

  static Uri predictUri() {
    final normalizedBaseUrl = baseUrl.endsWith('/')
        ? baseUrl.substring(0, baseUrl.length - 1)
        : baseUrl;
    return Uri.parse('$normalizedBaseUrl/predict');
  }
}

class CropYieldApp extends StatelessWidget {
  const CropYieldApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Crop Yield Predictor',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF0F766E),
        ),
      ),
      home: const CropYieldHomePage(),
    );
  }
}

class CropYieldHomePage extends StatefulWidget {
  const CropYieldHomePage({super.key});

  @override
  State<CropYieldHomePage> createState() => _CropYieldHomePageState();
}

class _CropYieldHomePageState extends State<CropYieldHomePage> {
  static const Map<String, List<String>> _categoryOptions = {
    'Region': ['East', 'North', 'South', 'West'],
    'Soil_Type': ['Chalky', 'Clay', 'Loam', 'Peaty', 'Sandy', 'Silt'],
    'Crop': ['Barley', 'Cotton', 'Maize', 'Rice', 'Soybean', 'Wheat'],
    'Weather_Condition': ['Cloudy', 'Rainy', 'Sunny'],
  };

  static const Map<String, Map<String, num>> _numericBounds = {
    'Rainfall_mm': {'min': 100.00089622522204, 'max': 999.998098221668},
    'Temperature_Celsius': {'min': 15.000034141430271, 'max': 39.99999662316004},
    'Days_to_Harvest': {'min': 60, 'max': 149},
  };

  final Map<String, TextEditingController> _controllers = {
    'Region': TextEditingController(),
    'Soil_Type': TextEditingController(),
    'Crop': TextEditingController(),
    'Rainfall_mm': TextEditingController(),
    'Temperature_Celsius': TextEditingController(),
    'Fertilizer_Used': TextEditingController(),
    'Irrigation_Used': TextEditingController(),
    'Weather_Condition': TextEditingController(),
    'Days_to_Harvest': TextEditingController(),
  };

  String _statusText = 'Fill the fields, then tap Predict to call the API.';
  bool _isLoading = false;

  @override
  void dispose() {
    for (final controller in _controllers.values) {
      controller.dispose();
    }
    super.dispose();
  }

  String? _normalizeCategory(String key, String rawValue) {
    final normalized = rawValue.trim().toLowerCase();
    for (final option in _categoryOptions[key]!) {
      if (option.toLowerCase() == normalized) {
        return option;
      }
    }
    return null;
  }

  bool? _parseBool(String rawValue) {
    switch (rawValue.trim().toLowerCase()) {
      case 'true':
      case '1':
      case 'yes':
      case 'y':
        return true;
      case 'false':
      case '0':
      case 'no':
      case 'n':
        return false;
      default:
        return null;
    }
  }

  String? _validatePayload() {
    for (final entry in _controllers.entries) {
      if (entry.value.text.trim().isEmpty) {
        return 'Missing value for ${entry.key.replaceAll('_', ' ')}.';
      }
    }

    for (final category in _categoryOptions.keys) {
      if (_normalizeCategory(category, _controllers[category]!.text) == null) {
        return 'Invalid ${category.replaceAll('_', ' ')}. Use one of: ${_categoryOptions[category]!.join(', ')}.';
      }
    }

    final rainfall = double.tryParse(_controllers['Rainfall_mm']!.text.trim());
    final rainfallMin = _numericBounds['Rainfall_mm']!['min']!.toDouble();
    final rainfallMax = _numericBounds['Rainfall_mm']!['max']!.toDouble();
    if (rainfall == null || rainfall < rainfallMin || rainfall > rainfallMax) {
      return 'Rainfall must be between ${rainfallMin.toStringAsFixed(0)} and ${rainfallMax.toStringAsFixed(0)} mm.';
    }

    final temperature = double.tryParse(_controllers['Temperature_Celsius']!.text.trim());
    final temperatureMin = _numericBounds['Temperature_Celsius']!['min']!.toDouble();
    final temperatureMax = _numericBounds['Temperature_Celsius']!['max']!.toDouble();
    if (temperature == null || temperature < temperatureMin || temperature > temperatureMax) {
      return 'Temperature must be between ${temperatureMin.toStringAsFixed(0)} and ${temperatureMax.toStringAsFixed(0)} °C.';
    }

    final days = int.tryParse(_controllers['Days_to_Harvest']!.text.trim());
    final daysMin = _numericBounds['Days_to_Harvest']!['min']!.toInt();
    final daysMax = _numericBounds['Days_to_Harvest']!['max']!.toInt();
    if (days == null || days < daysMin || days > daysMax) {
      return 'Days to harvest must be between $daysMin and $daysMax.';
    }

    if (_parseBool(_controllers['Fertilizer_Used']!.text) == null) {
      return 'Fertilizer Used must be true or false.';
    }

    if (_parseBool(_controllers['Irrigation_Used']!.text) == null) {
      return 'Irrigation Used must be true or false.';
    }

    return null;
  }

  Map<String, dynamic> _buildPayload() {
    return <String, dynamic>{
      'Region': _normalizeCategory('Region', _controllers['Region']!.text)!,
      'Soil_Type': _normalizeCategory('Soil_Type', _controllers['Soil_Type']!.text)!,
      'Crop': _normalizeCategory('Crop', _controllers['Crop']!.text)!,
      'Rainfall_mm': double.parse(_controllers['Rainfall_mm']!.text.trim()),
      'Temperature_Celsius': double.parse(_controllers['Temperature_Celsius']!.text.trim()),
      'Fertilizer_Used': _parseBool(_controllers['Fertilizer_Used']!.text)!,
      'Irrigation_Used': _parseBool(_controllers['Irrigation_Used']!.text)!,
      'Weather_Condition': _normalizeCategory('Weather_Condition', _controllers['Weather_Condition']!.text)!,
      'Days_to_Harvest': int.parse(_controllers['Days_to_Harvest']!.text.trim()),
    };
  }

  String _buildErrorMessage(Object error) {
    if (error is http.ClientException) {
      return error.message;
    }
    return error.toString();
  }

  String _extractApiError(String responseBody) {
    try {
      final decoded = jsonDecode(responseBody);
      if (decoded is Map<String, dynamic>) {
        final detail = decoded['detail'];
        if (detail is String) {
          return detail;
        }
        if (detail is List) {
          return detail.map((item) => item.toString()).join('\n');
        }
        return decoded.toString();
      }
    } catch (_) {
      return responseBody;
    }
    return responseBody;
  }

  Future<void> _predictYield() async {
    final validationError = _validatePayload();
    if (validationError != null) {
      setState(() {
        _statusText = validationError;
      });
      return;
    }

    setState(() {
      _isLoading = true;
      _statusText = 'Sending request to the API...';
    });

    try {
      final response = await http.post(
        ApiConfig.predictUri(),
        headers: const {'Content-Type': 'application/json'},
        body: jsonEncode(_buildPayload()),
      );

      if (!mounted) {
        return;
      }

      if (response.statusCode >= 200 && response.statusCode < 300) {
        final decodedBody = jsonDecode(response.body) as Map<String, dynamic>;
        final predictedValue = (decodedBody['predicted_yield_tons_per_hectare'] as num).toDouble();
        setState(() {
          _statusText = 'Predicted yield: ${predictedValue.toStringAsFixed(2)} tons/hectare\nModel: ${decodedBody['model_name'] ?? 'unknown'}';
        });
      } else {
        setState(() {
          _statusText = _extractApiError(response.body).trim();
        });
      }
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _statusText = 'Request failed: ${_buildErrorMessage(error)}';
      });
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  Widget _buildField({
    required String label,
    required String hint,
    required TextInputType keyboardType,
    required String helperText,
  }) {
    return TextField(
      controller: _controllers[label],
      keyboardType: keyboardType,
      style: const TextStyle(fontSize: 16),
      decoration: InputDecoration(
        labelText: label.replaceAll('_', ' '),
        hintText: hint,
        helperText: helperText,
        helperStyle: const TextStyle(color: Color(0xFF64748B)),
        filled: true,
        fillColor: const Color(0xFFF8FAFC),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: Color(0xFFCBD5E1)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: Color(0xFF0F766E), width: 1.6),
        ),
      ),
    );
  }

  Widget _buildDropdownField({
    required String label,
    required List<String> options,
    required String helperText,
  }) {
    return DropdownButtonFormField<String>(
      value: _controllers[label]!.text.isEmpty ? null : _controllers[label]!.text,
      decoration: InputDecoration(
        labelText: label.replaceAll('_', ' '),
        helperText: helperText,
        helperStyle: const TextStyle(color: Color(0xFF64748B)),
        filled: true,
        fillColor: const Color(0xFFF8FAFC),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: Color(0xFFCBD5E1)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: Color(0xFF0F766E), width: 1.6),
        ),
      ),
      items: options
          .map(
            (option) => DropdownMenuItem<String>(
              value: option,
              child: Text(option),
            ),
          )
          .toList(),
      onChanged: (value) {
        if (value != null) {
          setState(() {
            _controllers[label]!.text = value;
          });
        }
      },
    );
  }

  Widget _buildBooleanField({
    required String label,
    required String helperText,
  }) {
    final selectedValue = _parseBool(_controllers[label]!.text);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFF8FAFC),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFE2E8F0)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label.replaceAll('_', ' '),
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 10,
            runSpacing: 8,
            children: [
              ChoiceChip(
                label: const Text('Yes'),
                selected: selectedValue == true,
                selectedColor: const Color(0xFFCCFBF1),
                labelStyle: TextStyle(
                  color: selectedValue == true ? const Color(0xFF0F766E) : const Color(0xFF334155),
                  fontWeight: FontWeight.w600,
                ),
                onSelected: (_) {
                  setState(() {
                    _controllers[label]!.text = 'true';
                  });
                },
              ),
              ChoiceChip(
                label: const Text('No'),
                selected: selectedValue == false,
                selectedColor: const Color(0xFFCCFBF1),
                labelStyle: TextStyle(
                  color: selectedValue == false ? const Color(0xFF0F766E) : const Color(0xFF334155),
                  fontWeight: FontWeight.w600,
                ),
                onSelected: (_) {
                  setState(() {
                    _controllers[label]!.text = 'false';
                  });
                },
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            helperText,
            style: const TextStyle(color: Color(0xFF64748B), fontSize: 12),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFFE6FFFB), Color(0xFFF8FAFC), Color(0xFFF1F5F9)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [Color(0xFF134E4A), Color(0xFF0F766E)],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: BorderRadius.circular(28),
                    boxShadow: const [
                      BoxShadow(
                        color: Color(0x1F134E4A),
                        blurRadius: 24,
                        offset: Offset(0, 12),
                      ),
                    ],
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.18),
                          borderRadius: BorderRadius.circular(16),
                        ),
                        child: const Icon(Icons.agriculture_rounded, color: Colors.white, size: 28),
                      ),
                      const SizedBox(width: 16),
                      const Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Crop Yield Predictor',
                              style: TextStyle(
                                color: Colors.white,
                                fontSize: 28,
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                            SizedBox(height: 8),
                            Text(
                              'Send crop, soil, weather, and farm inputs to the FastAPI model and receive a yield estimate.',
                              style: TextStyle(
                                color: Color(0xFFE2E8F0),
                                fontSize: 15,
                                height: 1.4,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 18),
                Card(
                  elevation: 0,
                  color: Colors.white.withOpacity(0.95),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(28)),
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            const Icon(Icons.tune_rounded, color: Color(0xFF0F766E)),
                            const SizedBox(width: 8),
                            Text(
                              'Prediction Inputs',
                              style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        const Text(
                          'Use the exact categories shown in the hints. The app validates numeric ranges before sending the request.',
                          style: TextStyle(color: Color(0xFF475569), height: 1.4),
                        ),
                        const SizedBox(height: 20),
                        _buildDropdownField(
                          label: 'Region',
                          options: _categoryOptions['Region']!,
                          helperText: 'Allowed: East, North, South, West',
                        ),
                        const SizedBox(height: 16),
                        _buildDropdownField(
                          label: 'Soil_Type',
                          options: _categoryOptions['Soil_Type']!,
                          helperText: 'Allowed: Chalky, Clay, Loam, Peaty, Sandy, Silt',
                        ),
                        const SizedBox(height: 16),
                        _buildDropdownField(
                          label: 'Crop',
                          options: _categoryOptions['Crop']!,
                          helperText: 'Allowed: Barley, Cotton, Maize, Rice, Soybean, Wheat',
                        ),
                        const SizedBox(height: 16),
                        Row(
                          children: [
                            Expanded(
                              child: _buildField(
                                label: 'Rainfall_mm',
                                hint: '750',
                                keyboardType: TextInputType.number,
                                helperText: '100 to 1000 mm',
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: _buildField(
                                label: 'Temperature_Celsius',
                                hint: '27',
                                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                                helperText: '15 to 40 °C',
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 16),
                        Column(
                          children: [
                            _buildBooleanField(
                              label: 'Fertilizer_Used',
                              helperText: 'Choose true or false',
                            ),
                            const SizedBox(height: 12),
                            _buildBooleanField(
                              label: 'Irrigation_Used',
                              helperText: 'Choose true or false',
                            ),
                          ],
                        ),
                        const SizedBox(height: 16),
                        _buildDropdownField(
                          label: 'Weather_Condition',
                          options: _categoryOptions['Weather_Condition']!,
                          helperText: 'Allowed: Cloudy, Rainy, Sunny',
                        ),
                        const SizedBox(height: 16),
                        _buildField(
                          label: 'Days_to_Harvest',
                          hint: '110',
                          keyboardType: TextInputType.number,
                          helperText: '60 to 149 days',
                        ),
                        const SizedBox(height: 20),
                        SizedBox(
                          width: double.infinity,
                          height: 54,
                          child: FilledButton.icon(
                            onPressed: _isLoading ? null : _predictYield,
                            style: FilledButton.styleFrom(
                              backgroundColor: const Color(0xFF0F766E),
                              foregroundColor: Colors.white,
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                              elevation: 0,
                            ),
                            icon: _isLoading
                                ? const SizedBox(
                                    height: 18,
                                    width: 18,
                                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                                  )
                                : const Icon(Icons.insights),
                            label: Text(_isLoading ? 'Predicting...' : 'Predict Yield'),
                          ),
                        ),
                        const SizedBox(height: 18),
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(18),
                          decoration: BoxDecoration(
                            color: const Color(0xFFF8FAFC),
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(color: const Color(0xFFE2E8F0)),
                          ),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Container(
                                padding: const EdgeInsets.all(10),
                                decoration: BoxDecoration(
                                  color: const Color(0xFFCCFBF1),
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: const Icon(Icons.auto_graph_rounded, color: Color(0xFF0F766E)),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Text(
                                  _statusText,
                                  style: const TextStyle(
                                    fontSize: 15,
                                    color: Color(0xFF0F172A),
                                    height: 1.5,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
