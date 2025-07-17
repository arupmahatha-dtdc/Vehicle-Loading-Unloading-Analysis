import csv
import os

class UnitConverter:
    def __init__(self, csv_path=None):
        if csv_path is None:
            csv_path = os.path.join(os.path.dirname(__file__), 'data', 'unit_conversion.csv')
        self.conversion_table = self._load_conversion_table(csv_path)
        self.units = list(self.conversion_table.keys())

    def _load_conversion_table(self, csv_path):
        table = {}
        with open(csv_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                from_unit = row['From\\To']
                table[from_unit] = {unit: float(row[unit]) for unit in reader.fieldnames if unit != 'From\\To'}
        return table

    def convert(self, value, from_unit, to_unit):
        if from_unit not in self.conversion_table:
            raise ValueError(f"Unknown from_unit: {from_unit}")
        if to_unit not in self.conversion_table[from_unit]:
            raise ValueError(f"Unknown to_unit: {to_unit}")
        return value * self.conversion_table[from_unit][to_unit]

    def feet_to_meters(self, value):
        return self.convert(value, 'ft', 'm')

# Example usage:
if __name__ == "__main__":
    converter = UnitConverter()
    print("10 cm to in:", converter.convert(10, 'cm', 'in')) 