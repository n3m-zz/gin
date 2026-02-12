import sys
import subprocess
import argparse
import csv
import re
import os
from datetime import datetime

def run_perf_measurement(command):
    """
    Executa o comando dentro do 'perf stat' e retorna os dados brutos.
    O flag -x, força a saída em formato CSV para facilitar o parsing.
    """
    # Monta o comando perf.
    # -e: especifica os eventos (energia, tempo total, user e system time)
    # -x,: usa vírgula como separador
    # -a: conta em todas as CPUs (necessário para energia) ou per-process se possível
    # Nota: user_time e system_time são calculados pelo perf stat padrão, 
    # mas para CSV limpo, vamos pegar o output padrão e parsear ou usar eventos específicos se disponíveis.
    
    # Estratégia mais robusta para o Sérgio: Usar o output padrão do perf stat -x
    perf_cmd = [
        "perf", "stat", 
        "-e", "power/energy-pkg/",
        "-x", ",",  # Saída separada por vírgula
        "sh", "-c", command # Roda o comando num shell
    ]

    print(f"--- Executando Perf para: '{command}' ---")
    
    # Executa. O output do perf vai para o stderr por padrão.
    result = subprocess.run(perf_cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("Erro ao executar o comando ou o perf:")
        print(result.stderr)
        return None

    return result.stderr

def parse_perf_output(perf_output):
    """
    Lê a saída CSV do perf e extrai os valores.
    Formato típico do perf -x,:
    valor,unidade,evento,variancia,...
    """
    data = {
        "energy_joules": 0.0,
        "duration_time": 0.0,
        "user_time": 0.0,
        "system_time": 0.0
    }
    
    # O perf retorna user e sys time como "task-clock" ou separado dependendo da versão.
    # Vamos pegar o que estiver disponível.
    
    for line in perf_output.splitlines():
        parts = line.split(',')
        if len(parts) < 3:
            continue
            
        try:
            val_str = parts[0]
            if val_str == "<not supported>": continue
            value = float(val_str)
            event = parts[2]
            
            if "power/energy-pkg/" in event:
                data["energy_joules"] = value
            elif "task-clock" in event: # As vezes user+sys vem aqui, mas vamos confiar no duration_time
                pass 
            
        except ValueError:
            continue

    # O perf stat no final do stderr imprime o tempo "real", "user" e "sys" 
    # se não usarmos o modo -x estrito. Mas com -x, ele foca nos eventos.
    # Truque: Para obter user e sys separados com precisão no formato CSV, 
    # o jeito mais fácil é parsear o output TEXTUAL padrão do perf, não o CSV (-x), 
    # pois o CSV do perf as vezes omite o resumo de user/sys.
    
    return data

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cmd', required=True)
    parser.add_argument('--output', default='energy_results.csv')
    args = parser.parse_args()

    # Usamos LC_NUMERIC=C para garantir que o perf use ponto para decimais, não vírgula
    my_env = os.environ.copy()
    my_env["LC_NUMERIC"] = "C"

    # Comando ajustado para garantir user e sys time
    # O comando `time` do linux (não o do bash) dá o user/sys/real facilmente.
    # Mas o Sérgio quer o PERF.
    # O perf stat reporta "seconds user" e "seconds sys" no final.
    
    cmd_list = ["perf", "stat", "-e", "power/energy-pkg/", "sh", "-c", args.cmd]
    
    # Roda o perf sem o -x para pegar o resumo legível que contém user/sys
    proc = subprocess.run(cmd_list, capture_output=True, text=True, env=my_env)
    
    output = proc.stderr
    print(output) # Mostra no log do CI para debug

    # Regex para capturar os dados do texto padrão do perf
    # Padrão: "  12.34 Joules power/energy-pkg/ ..."
    # Padrão: "  0.56 seconds user"
    # Padrão: "  0.12 seconds sys"
    # Padrão: "  10.02 seconds time elapsed"
    
    energy = re.search(r"([\d\.]+)\s+Joules\s+power\/energy-pkg\/", output)
    t_user = re.search(r"([\d\.]+)\s+seconds user", output)
    t_sys  = re.search(r"([\d\.]+)\s+seconds sys", output)
    t_real = re.search(r"([\d\.]+)\s+seconds time elapsed", output)

    results = {
        "timestamp": datetime.now().isoformat(),
        "command": args.cmd,
        "energy_joules": energy.group(1) if energy else "0",
        "user_time": t_user.group(1) if t_user else "0",
        "system_time": t_sys.group(1) if t_sys else "0",
        "duration_time": t_real.group(1) if t_real else "0"
    }

    # Salva no CSV
    file_exists = os.path.isfile(args.output)
    with open(args.output, "a", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=results.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(results)

if __name__ == "__main__":
    main()