from binance.client import Client
import pandas as pd
import numpy as np
from datetime import datetime
import logging

class MarketExpert:
    def __init__(self):
        self.client = Client()
        
    def get_complete_history(self):
        """Obtém histórico completo do Bitcoin"""
        print("Obtendo histórico completo do BTC/USDT...")
        
        # Dados históricos diários desde o início
        historical_klines = self.client.get_historical_klines(
            "BTCUSDT",
            Client.KLINE_INTERVAL_1DAY,
            "1 Jan, 2017"
        )
        
        # Converte para DataFrame
        df = pd.DataFrame(historical_klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 
            'volume', 'close_time', 'quote_volume', 'trades',
            'taker_buy_base', 'taker_buy_quote', 'ignored'
        ])
        
        # Prepara dados
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        return df
        
    def analyze_market_cycles(self, df):
        """Analisa ciclos de mercado"""
        # Garante que o índice é datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        
        # Reduz período para detectar ciclos menores
        df = df.tail(365)  # Último ano
        
        min_cycle_days = 30  # Reduzido para ciclos mais curtos
        price_threshold = 0.15  # 15% de correção
        
        cycles = []
        current_cycle = {
            'start': df.index[0],
            'bottom': float('inf'),
            'top': 0
        }
        
        for date, row in df.iterrows():
            price = float(row['close'])
            
            # Atualiza máximas e mínimas
            current_cycle['bottom'] = min(current_cycle['bottom'], price)
            current_cycle['top'] = max(current_cycle['top'], price)
            
            # Detecta novo ciclo
            try:
                days_diff = (date - current_cycle['start']).days
                if price < current_cycle['top'] * (1 - price_threshold):
                    if len(cycles) == 0 or days_diff >= min_cycle_days:
                        cycles.append(current_cycle)
                        current_cycle = {'start': date, 'bottom': price, 'top': price}
            except Exception as e:
                print(f"Erro ao processar data: {e}")
                continue
        
        # Adiciona ciclo atual se relevante
        if current_cycle['top'] > current_cycle['bottom'] * 1.1:  # 10% de movimento
            cycles.append(current_cycle)
        
        return cycles
        
    def generate_expert_analysis(self):
        """Gera análise profissional completa"""
        df = self.get_complete_history()
        cycles = self.analyze_market_cycles(df)
        
        current_price = float(df['close'].iloc[-1])
        all_time_high = float(df['close'].max())
        
        # Prepara dados do último ciclo
        last_cycle_info = ""
        if cycles:
            last_cycle = cycles[-1]
            last_cycle_info = f"""
            Total de Ciclos Identificados: {len(cycles)}
            Último Ciclo:
            - Início: {last_cycle['start'].strftime('%d/%m/%Y')}
            - Mínima: ${last_cycle['bottom']:,.2f}
            - Máxima: ${last_cycle['top']:,.2f}
            - Variação: {((last_cycle['top'] - last_cycle['bottom']) / last_cycle['bottom'] * 100):.2f}%
            """
        else:
            last_cycle_info = """
            Análise de Ciclos:
            - Ciclos insuficientes para análise
            - Aguardando formação de padrão
            """
        
        analysis = f"""
            === Análise Profissional do Bitcoin ===
            Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}
            
            1. VISÃO MACRO
            --------------
            Preço Atual: ${current_price:,.2f}
            Máxima Histórica: ${all_time_high:,.2f}
            Distância da Máxima: {((all_time_high - current_price) / all_time_high * 100):.2f}%
            
            2. CICLOS DE MERCADO
            -------------------
            {last_cycle_info}
            
            3. ANÁLISE TÉCNICA
            ----------------
            {self.technical_analysis(df)}
            
            4. NÍVEIS IMPORTANTES
            -------------------
            {self.identify_key_levels(df)}
            
            5. CONCLUSÃO
            -----------
            {self.generate_conclusion(df, cycles, current_price)}
            """
        
        return analysis
        
    def technical_analysis(self, df):
        """Análise técnica detalhada"""
        recent_df = df.tail(90)  # Últimos 90 dias
        
        trend = self.identify_trend(recent_df)
        momentum = self.calculate_momentum(recent_df)
        volume_analysis = self.analyze_volume(recent_df)
        
        return f"""
        Tendência Atual: {trend['direction']}
        Força da Tendência: {trend['strength']}
        Momentum: {momentum}
        Volume: {volume_analysis}
        """
        
    def identify_key_levels(self, df):
        """Identifica níveis importantes"""
        current_price = float(df['close'].iloc[-1])
        
        # Encontra suportes e resistências
        levels = self.find_support_resistance(df)
        
        return f"""
        Suportes:
        {self.format_levels(levels['supports'], current_price)}
        
        Resistências:
        {self.format_levels(levels['resistances'], current_price)}
        """
        
    def generate_conclusion(self, df, cycles, current_price):
        """Gera conclusão baseada em análise completa"""
        cycle_position = "INDEFINIDO" if not cycles else self.identify_cycle_position(df, cycles)
        risk_reward = self.calculate_risk_reward(df)
        
        # Calcula RSI
        try:
            rsi = self.calculate_rsi(df)
            rsi_info = f"RSI: {rsi:.2f}"
        except:
            rsi_info = "RSI: Indisponível"
        
        conclusion = f"""
            Posição no Ciclo: {cycle_position}
            Relação Risco/Retorno: {risk_reward}
            {rsi_info}
            
            Recomendação:
            {self.generate_recommendation(df, cycles, current_price)}
            """
        
        return conclusion
        
    def identify_trend(self, df):
        """Identifica tendência atual"""
        # Calcula médias móveis
        df['SMA20'] = df['close'].rolling(window=20).mean()
        df['SMA50'] = df['close'].rolling(window=50).mean()
        
        current_price = df['close'].iloc[-1]
        sma20 = df['SMA20'].iloc[-1]
        sma50 = df['SMA50'].iloc[-1]
        
        # Determina direção
        if current_price > sma20 and sma20 > sma50:
            direction = "ALTA"
            strength = "FORTE"
        elif current_price > sma20 and sma20 < sma50:
            direction = "ALTA"
            strength = "MODERADA"
        elif current_price < sma20 and sma20 > sma50:
            direction = "BAIXA"
            strength = "MODERADA"
        else:
            direction = "BAIXA"
            strength = "FORTE"
            
        return {
            'direction': direction,
            'strength': strength
        }
        
    def calculate_momentum(self, df):
        """Calcula momentum do mercado"""
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        current_rsi = rsi.iloc[-1]
        
        if current_rsi > 70:
            return "SOBRECOMPRADO"
        elif current_rsi < 30:
            return "SOBREVENDIDO"
        else:
            return "NEUTRO"
            
    def analyze_volume(self, df):
        """Analisa volume de negociação"""
        avg_volume = df['volume'].mean()
        current_volume = df['volume'].iloc[-1]
        
        volume_ratio = current_volume / avg_volume
        
        if volume_ratio > 1.5:
            return "ALTO"
        elif volume_ratio < 0.5:
            return "BAIXO"
        else:
            return "NORMAL"
            
    def find_support_resistance(self, df):
        """Encontra níveis de suporte e resistência"""
        df = df.tail(90)
        current_price = df['close'].iloc[-1]
        
        # Calcula níveis técnicos
        sma20 = df['close'].rolling(window=20).mean().iloc[-1]
        sma50 = df['close'].rolling(window=50).mean().iloc[-1]
        sma200 = df['close'].rolling(window=200).mean().iloc[-1]
        
        # Calcula Fibonacci do último movimento
        high = df['high'].max()
        low = df['low'].min()
        fib_levels = {
            0.236: high - (high - low) * 0.236,
            0.382: high - (high - low) * 0.382,
            0.618: high - (high - low) * 0.618,
        }
        
        # Identifica níveis
        supports = []
        resistances = []
        
        # Adiciona médias móveis
        for ma in [sma20, sma50, sma200]:
            if ma < current_price:
                supports.append(ma)
            else:
                resistances.append(ma)
        
        # Adiciona níveis Fibonacci
        for level in fib_levels.values():
            if level < current_price:
                supports.append(level)
            else:
                resistances.append(level)
        
        # Adiciona mínimas e máximas recentes
        supports.extend(df['low'].nsmallest(3))
        resistances.extend(df['high'].nlargest(3))
        
        return {
            'supports': sorted(set([s for s in supports if s < current_price]))[-3:],
            'resistances': sorted(set([r for r in resistances if r > current_price]))[:3]
        }
        
    def format_levels(self, levels, current_price):
        """Formata níveis para exibição"""
        formatted = []
        for level in levels:
            distance = abs(level - current_price) / current_price * 100
            formatted.append(f"${level:,.2f} ({distance:.2f}% do preço atual)")
        return "\n".join(formatted)
        
    def identify_cycle_position(self, df, cycles):
        """Identifica posição no ciclo atual"""
        if not cycles:
            return "INDEFINIDO"
            
        current_price = df['close'].iloc[-1]
        last_cycle = cycles[-1]
        
        # Calcula posição relativa
        range_size = last_cycle['top'] - last_cycle['bottom']
        position = (current_price - last_cycle['bottom']) / range_size
        
        if position < 0.2:
            return "INÍCIO DE CICLO"
        elif position < 0.4:
            return "ACUMULAÇÃO"
        elif position < 0.6:
            return "MEIO DE CICLO"
        elif position < 0.8:
            return "DISTRIBUIÇÃO"
        else:
            return "FIM DE CICLO"
            
    def calculate_risk_reward(self, df):
        """Calcula relação risco/retorno atual"""
        current_price = df['close'].iloc[-1]
        
        # Encontra próxima resistência e suporte
        levels = self.find_support_resistance(df)
        
        if not levels['resistances'] or not levels['supports']:
            return "INDEFINIDO"
            
        next_resistance = min(levels['resistances'])
        next_support = max(levels['supports'])
        
        reward = (next_resistance - current_price) / current_price
        risk = (current_price - next_support) / current_price
        
        if risk == 0:
            return "INDEFINIDO"
            
        ratio = reward / risk
        
        if ratio > 3:
            return "EXCELENTE"
        elif ratio > 2:
            return "BOA"
        elif ratio > 1:
            return "MODERADA"
        else:
            return "DESFAVORÁVEL"
            
    def generate_recommendation(self, df, cycles, current_price):
        """Gera recomendação mais detalhada"""
        trend = self.identify_trend(df)
        rsi = self.calculate_rsi(df)
        volume_status = self.analyze_volume(df)
        
        # Análise mais profunda
        recommendation = ""
        risk_level = "ALTO"  # Default
        
        if trend['direction'] == "ALTA":
            if rsi < 70:  # Não sobrecomprado
                if volume_status != "BAIXO":
                    risk_level = "MODERADO"
                    recommendation = "COMPRA MODERADA - Tendência de alta com volume adequado"
                else:
                    recommendation = "AGUARDAR - Volume insuficiente para confirmar movimento"
            else:
                recommendation = "AGUARDAR - Mercado sobrecomprado"
        else:
            if rsi > 30:  # Não sobrevendido
                if volume_status == "ALTO":
                    risk_level = "MODERADO"
                    recommendation = "VENDA MODERADA - Correção com volume"
                else:
                    recommendation = "AGUARDAR - Sem confirmação de volume"
            else:
                recommendation = "NEUTRO - Mercado sobrevendido"
        
        return f"""
        {recommendation}
        
        Indicadores:
        - RSI: {rsi:.2f}
        - Volume: {volume_status}
        - Risco: {risk_level}
        """
        
    def calculate_rsi(self, df):
        """Calcula RSI atual"""
        try:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1]
        except:
            return 50  # valor neutro em caso de erro
        
    def get_historical_high(self):
        """Obtém máxima histórica atualizada"""
        try:
            # Obtém dados mais recentes
            klines = self.client.get_klines(
                symbol="BTCUSDT",
                interval=Client.KLINE_INTERVAL_1MINUTE,
                limit=1440  # Últimas 24h
            )
            
            # Converte para DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close',
                'volume', 'close_time', 'quote_volume', 'trades',
                'taker_buy_base', 'taker_buy_quote', 'ignored'
            ])
            
            # Atualiza máxima
            current_high = float(df['high'].max())
            stored_high = 104000.00  # Nova máxima histórica
            
            return max(current_high, stored_high)
            
        except Exception as e:
            logging.error(f"Erro ao obter máxima histórica: {e}")
            return 104000.00  # Retorna máxima conhecida em caso de erro