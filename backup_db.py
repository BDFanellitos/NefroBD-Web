import bd
import time
import schedule

def backup_automatico():
    """Faz backup automático a cada hora"""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Fazendo backup automático...")
    if bd.sincronizar_usuarios():
        print("Backup realizado com sucesso!")
    else:
        print("Erro no backup!")

if __name__ == "__main__":
    # Fazer backup a cada hora
    schedule.every(1).hours.do(backup_automatico)
    
    print("Serviço de backup iniciado...")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Verificar a cada minuto