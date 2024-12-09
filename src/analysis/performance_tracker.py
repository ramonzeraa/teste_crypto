import pandas as pd

class PerformanceTracker:
    def __init__(self):
        self.metrics = {
            'learning_rate': [],
            'confidence_levels': [],
            'pattern_recognition': [],
            'win_rate': [],
            'risk_analysis': [],
            'market_adaptation': []
        }
    
    def export_to_powerbi(self):
        # Exporta dados formatados para Power BI
        df = pd.DataFrame(self.metrics)
        df.to_csv('bot_performance.csv') 