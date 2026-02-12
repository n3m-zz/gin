import subprocess
import time
import os
import csv

def read_energy():
    # Caminho padrão para o consumo total do pacote da CPU (Package 0)
    path = "/sys/class/powercap/intel-rapl:0/energy_uj"
    with open(path, 'r') as f:
        return int(f.read())

def run_experiment(command):
    # Coleta energia inicial
    energy_start = read_energy()
    start_time = time.time()

    # Executa o comando de ML (ex: pytest ou python train.py)
    process = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    # Coleta energia final
    energy_end = read_energy()
    end_time = time.time()

    # Cálculos
    total_energy_uj = energy_end - energy_start
    total_energy_j = total_energy_uj / 1_000_000  # Converte para Joules
    duration = end_time - start_time
    
    return {
        "energy_j": total_energy_j,
        "duration_s": duration,
        "stdout": process.stdout
    }

if __name__ == "__main__":
    # Exemplo de uso para o seu ambiente de CI
    cmd = "pytest tests/ml_model.py" # Ou o comando que você definiu no YAML
    print(f"Iniciando medição para: {cmd}")
    
    results = run_experiment(cmd)
    
    # Salva em CSV para o seu Artifact do GitHub
    with open('resultados_energia.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Comando", "Energia_Joules", "Tempo_Segundos"])
        writer.writerow([cmd, results["energy_j"], results["duration_s"]])

    print(f"Consumo Total: {results['energy_j']:.2f} Joules")