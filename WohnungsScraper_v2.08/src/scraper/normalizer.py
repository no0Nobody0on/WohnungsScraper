"""
WohnungsScraper - Address Normalizer
Hilfsfunktionen zur Normalisierung von Adressen
"""

import re
from typing import List, Set


class AddressNormalizer:
    UMLAUT_MAP = {
        'ae': 'ae', 'oe': 'oe', 'ue': 'ue', 'ss': 'ss', 
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss'
    }
    
    @staticmethod
    def normalize(text: str) -> str:
        if not text:
            return ""
        result = text.lower().strip()
        # Umlaute ersetzen
        for uml, repl in AddressNormalizer.UMLAUT_MAP.items():
            result = result.replace(uml, repl)
        # Strassen-Abkuerzungen (str. -> strasse)
        result = re.sub(r'str\.(\s|$)', r'strasse\1', result)
        result = re.sub(r'str(\s|$)', r'strasse\1', result)
        result = re.sub(r'strasse(\s|$)', r'strasse\1', result)
        # Bindestriche und Sonderzeichen
        result = result.replace('-', ' ')
        result = re.sub(r'[^\w\s]', ' ', result)
        result = re.sub(r'\s+', ' ', result).strip()
        return result
    
    @staticmethod
    def get_street_variants(street: str) -> List[str]:
        variants = []
        base = AddressNormalizer.normalize(street)
        variants.append(base)
        if base.endswith('strasse'):
            variants.append(base[:-7].strip())
        return variants
    
    @staticmethod
    def get_house_variants(house_number: str) -> Set[str]:
        variants = set()
        hn = house_number.strip().lower()
        range_match = re.match(r'(\d+)\s*[-/]\s*(\d+)', hn)
        if range_match:
            start, end = int(range_match.group(1)), int(range_match.group(2))
            is_even = start % 2 == 0
            for num in range(start, end + 1):
                if (num % 2 == 0) == is_even:
                    variants.add(str(num))
        else:
            match = re.match(r'(\d+)\s*([a-z])?', hn)
            if match:
                num = match.group(1)
                suffix = match.group(2)
                variants.add(num)
                if suffix:
                    variants.add(f"{num}{suffix}")
                    variants.add(f"{num} {suffix}")
        return variants if variants else {hn}
