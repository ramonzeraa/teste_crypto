from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import json
from twilio.rest import Client
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

class SystemMonitor:
    def __init__(self, twilio_sid: str, twilio_token: str, 
                 whatsapp_from: str, whatsapp_to: str,
                 alert_interval: int = 300):
        """Inicializa o monitor do sistema"""
        self.logger = logging.getLogger('system_monitor')
        self.twilio_sid = twilio_sid
        self.twilio_token = twilio_token
        self.whatsapp_from = whatsapp_from
        self.whatsapp_to = whatsapp_to
        self.alert_interval = alert_interval
        
        # Inicializa métricas
        self.metrics = {}
        self.errors = []  # Lista de erros
        self.max_errors = 1000  # Máximo de erros armazenados
        self.last_alert_time = time.time()
        self.start_time = time.time()
        
        self.logger.info("Monitor do sistema inicializado")
        
        self.twilio_client = Client(twilio_sid, twilio_token)
        self.whatsapp_from = whatsapp_from.replace('whatsapp:', '')
        self.whatsapp_to = whatsapp_to.replace('whatsapp:', '')
        self.whatsapp_from = f"whatsapp:{self.whatsapp_from}"
        self.whatsapp_to = f"whatsapp:{self.whatsapp_to}"
        self.metrics_history = []
        self.alerts = []
        self.system_status = {
            'is_trading': False,
            'last_update': None,
            'errors': [],
            'warnings': []
        }
        
        # Limites para alertas
        self.thresholds = {
            'profit_warning': -0.02,    # -2%
            'profit_critical': -0.05,   # -5%
            'latency_warning': 2.0,     # 2 segundos
            'memory_warning': 0.85,     # 85% uso
            'api_errors_threshold': 3    # 3 erros em 1 hora
        }
        
        self.last_alert_time = {}
        self.alert_cooldown = 300  # 5 minutos entre alertas do mesmo tipo
        
        self.alert_thresholds = {
            'error': 0,  # Sempre alerta
            'warning': 300,  # 5 minutos
            'info': 3600  # 1 hora
        }
    
    def send_whatsapp(self, message: str, media_url: Optional[str] = None):
        """Envia mensagem via WhatsApp"""
        try:
            if media_url:
                self.twilio_client.messages.create(
                    from_=self.whatsapp_from,
                    to=self.whatsapp_to,
                    body=message,
                    media_url=[media_url]
                )
            else:
                self.twilio_client.messages.create(
                    from_=self.whatsapp_from,
                    to=self.whatsapp_to,
                    body=message
                )
            
        except Exception as e:
            logging.error(f"Erro ao enviar WhatsApp: {e}")
    
    def update_status(self, metrics: Dict):
        """Atualiza status do sistema"""
        try:
            current_time = datetime.now()
            
            # Atualiza métricas
            metrics['timestamp'] = current_time
            self.metrics_history.append(metrics)
            
            # Limita histórico
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-1000:]
            
            # Verifica condições de alerta
            self._check_alerts(metrics)
            
            # Atualiza status
            self.system_status['last_update'] = current_time
            self.system_status['is_trading'] = metrics.get('is_trading', False)
            
        except Exception as e:
            logging.error(f"Erro ao atualizar status: {e}")
            self.send_alert(f"❌ Erro no monitoramento: {str(e)}", "high")
    
    def send_alert(self, message: str, priority: str = "normal"):
        """Envia alerta via WhatsApp"""
        try:
            # Emojis baseados na prioridade
            priority_emojis = {
                "low": "ℹ️",
                "normal": "⚠️",
                "high": "🚨"
            }
            
            emoji = priority_emojis.get(priority, "���️")
            formatted_message = f"{emoji} {message}\n\nHorário: {datetime.now()}"
            
            self.send_whatsapp(formatted_message)
            
            self.alerts.append({
                'timestamp': datetime.now(),
                'message': message,
                'priority': priority
            })
            
        except Exception as e:
            logging.error(f"Erro ao enviar alerta: {e}")
    
    def send_performance_report(self, performance_data: Dict):
        """Envia relatório de performance"""
        try:
            # Gera gráficos
            fig = self._generate_performance_charts(performance_data)
            
            # Salva temporariamente
            chart_path = 'temp_performance_chart.png'
            fig.write_image(chart_path)
            
            # Prepara mensagem
            report = (
                "📊 *Relatório de Performance*\n\n"
                f"💰 Lucro Total: {performance_data['total_profit']:.2%}\n"
                f"📈 Win Rate: {performance_data['win_rate']:.2%}\n"
                f"📉 Drawdown Máx: {performance_data['max_drawdown']:.2%}\n"
                f"🎯 Trades Totais: {performance_data['total_trades']}\n"
                f"⚖️ Profit Factor: {performance_data['profit_factor']:.2f}\n"
            )
            
            # Upload da imagem para um servidor (exemplo com imgur)
            # Você precisará implementar o upload da imagem
            chart_url = self._upload_chart(chart_path)
            
            # Envia mensagem e gráfico
            self.send_whatsapp(report, chart_url)
            
        except Exception as e:
            logging.error(f"Erro ao enviar relatório: {e}")
            self.send_alert(f"Erro ao gerar relatório: {str(e)}", "high") 
    
    def send_divergence_alert(self, analysis: Dict):
        """Envia alerta de divergência"""
        try:
            divergences = analysis.get('technical', {}).get('divergences', {})
            if divergences.get('severity') in ['medium', 'high']:
                current_time = datetime.now()
                
                # Verifica cooldown
                if ('divergence' in self.last_alert_time and 
                    (current_time - self.last_alert_time['divergence']).seconds < self.alert_cooldown):
                    return
                
                # Prepara mensagem
                message = "⚠️ Alerta de Divergência!\n\n"
                
                if divergences.get('price_rsi'):
                    message += "- Divergência Preço/RSI detectada\n"
                if divergences.get('price_macd'):
                    message += "- Divergência Preço/MACD detectada\n"
                if divergences.get('indicators_sentiment'):
                    message += "- Divergência Indicadores/Sentimento detectada\n"
                
                message += f"\nSeveridade: {divergences['severity'].upper()}"
                
                # Adiciona dados técnicos
                tech = analysis.get('technical', {})
                message += f"\n\nRSI: {tech.get('rsi', {}).get('value', 0):.2f}"
                message += f"\nTendência: {tech.get('trend', 'neutral')}"
                message += f"\nForça: {tech.get('trend_strength', 0):.2f}"
                
                self.send_alert(message)
                self.last_alert_time['divergence'] = current_time
                
        except Exception as e:
            logging.error(f"Erro ao enviar alerta de divergência: {e}")
    
    def update_metrics(self, data: Dict):
        """Atualiza métricas do sistema"""
        try:
            self.metrics.update({
                'execution_latency': self._calculate_latency(),
                'signal_quality': self._evaluate_signal_quality(data),
                'risk_exposure': self._calculate_risk_exposure(data),
                'market_conditions': self._analyze_market_conditions(data),
                'system_health': self._check_system_health(),
                'last_update': datetime.now()
            })
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar métricas: {e}")

    def _calculate_latency(self) -> float:
        """Calcula latência de execução"""
        try:
            return time.time() - self.start_time
        except Exception as e:
            self.logger.error(f"Erro ao calcular latência: {e}")
            return 0.0

    def _evaluate_signal_quality(self, data: Dict) -> float:
        """Avalia qualidade dos sinais"""
        try:
            if not data or 'technical' not in data:
                return 0.0
            
            # Analisa consistência dos sinais
            signals = data.get('technical', {})
            consistency = sum(1 for sig in signals.values() if isinstance(sig, dict))
            return min(consistency / max(len(signals), 1), 1.0)
            
        except Exception as e:
            self.logger.error(f"Erro ao avaliar sinais: {e}")
            return 0.0

    def _calculate_risk_exposure(self, data: Dict) -> float:
        """Calcula exposição ao risco"""
        try:
            if not data or 'risk' not in data:
                return 0.0
            
            risk_metrics = data.get('risk', {})
            total_risk = sum(
                value for key, value in risk_metrics.items()
                if isinstance(value, (int, float))
            )
            return min(total_risk / max(len(risk_metrics), 1), 1.0)
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular risco: {e}")
            return 0.0

    def _analyze_market_conditions(self, data: Dict) -> Dict:
        """Analisa condições de mercado"""
        try:
            return {
                'volatility': data.get('technical', {}).get('volatility', 0),
                'trend_strength': data.get('technical', {}).get('trend_strength', 0),
                'market_phase': self._determine_market_phase(data)
            }
        except Exception as e:
            self.logger.error(f"Erro ao analisar mercado: {e}")
            return {}

    def _determine_market_phase(self, data: Dict) -> str:
        """Determina fase do mercado"""
        try:
            if not data or 'technical' not in data:
                return 'unknown'
            
            tech = data['technical']
            if tech.get('trend_strength', 0) > 0.7:
                return 'trending'
            elif tech.get('volatility', 0) > 0.7:
                return 'volatile'
            else:
                return 'ranging'
                
        except Exception as e:
            self.logger.error(f"Erro ao determinar fase: {e}")
            return 'unknown'

    def _check_system_health(self) -> Dict:
        """Verifica saúde do sistema"""
        try:
            return {
                'memory_usage': self._get_memory_usage(),
                'cpu_usage': self._get_cpu_usage(),
                'error_rate': len(self.errors) / max((time.time() - self.start_time) / 3600, 1),
                'uptime': time.time() - self.start_time
            }
        except Exception as e:
            self.logger.error(f"Erro ao verificar saúde: {e}")
            return {}

    def _get_memory_usage(self) -> float:
        """Obtém uso de memória"""
        try:
            import psutil
            return psutil.Process().memory_percent()
        except:
            return 0.0

    def _get_cpu_usage(self) -> float:
        """Obtém uso de CPU"""
        try:
            import psutil
            return psutil.Process().cpu_percent()
        except:
            return 0.0

    def report_error(self, error_type: str, error_message: str):
        """Reporta erros do sistema"""
        try:
            error_data = {
                'type': error_type,
                'message': error_message,
                'timestamp': datetime.now()
            }
            
            self.errors.append(error_data)
            
            if len(self.errors) > self.max_errors:
                self.errors = self.errors[-self.max_errors:]
            
            if self._should_send_alert(error_type):
                self._send_alert(
                    f"Erro: {error_type}",
                    f"Mensagem: {error_message}\nTimestamp: {datetime.now()}"
                )
            
        except Exception as e:
            self.logger.error(f"Erro ao reportar erro: {e}")

    def _should_send_alert(self, error_type: str) -> bool:
        """Verifica se deve enviar alerta"""
        try:
            current_time = time.time()
            threshold = self.alert_thresholds.get(error_type.lower(), 300)
            
            if current_time - float(self.last_alert_time) >= threshold:
                self.last_alert_time = current_time
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar alerta: {e}")
            return False

    def _send_alert(self, title: str, message: str):
        """Envia alerta via WhatsApp"""
        try:
            # Implementação do envio via Twilio aqui
            self.logger.info(f"Alerta: {title} - {message}")
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar alerta: {e}")

    def check_alerts(self):
        """Verifica condições de alerta"""
        try:
            if not self.metrics:
                return
            
            # Verifica métricas de risco
            risk_metrics = self.metrics.get('risk', {})
            if isinstance(risk_metrics, dict):  # Verifica se é um dicionário
                risk_score = float(risk_metrics.get('risk_score', 0))  # Converte para float com valor padrão
            else:
                risk_score = 0.0
            
            # Verifica se risco está alto
            if risk_score > 0.8:  # 80% de risco
                self.send_alert(
                    f"⚠️ Alerta de Risco Alto\n"
                    f"Score: {risk_score:.2%}"
                )
                
        except Exception as e:
            self.logger.error(f"Erro ao verificar alerta: {str(e)}")