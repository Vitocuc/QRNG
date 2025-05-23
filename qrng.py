# -*- coding: utf-8 -*-
"""QRNG.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1oFwhmdWycffmCrH-xljDIgfdcD1W_FC1

# Environment preparation
"""

# Commented out IPython magic to ensure Python compatibility.
# %pip install qiskit==1.2.4
# %pip install qiskit-ibm-runtime==0.30.0
# %pip install qiskit-aer==0.15.1
# %pip install qiskit-ibm-provider

# %pip install qiskit-algorithms==0.3.1

# %pip install matplotlib
# %pip install pylatexenc

# %pip install git+https://github.com/honno/sts-pylib.git # For the tests
# %pip install pyotp # For the OTPs

from IPython.display import clear_output
clear_output()

# Import of necessary libraries

#For the API key
from google.colab import userdata

from qiskit import QuantumCircuit, generate_preset_pass_manager
import numpy as np
from time import sleep

from qiskit.visualization import plot_histogram
from qiskit_ibm_runtime import SamplerV2 as Sampler
from qiskit_aer import Aer

from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_ibm_runtime.exceptions import IBMBackendError

# For the tests
from sts import *
from tabulate import tabulate
# For the OTPs
import pyotp

# Definiamo la classe usando la keyword 'class' seguita dal nome (convenzione: CamelCase)
class QRNG:
  """
  Questa è una stringa di documentazione (docstring).
  Descrive a cosa serve la classe. È una buona pratica includerla.
  """

  # --- Il Costruttore (__init__) ---
  # Questo metodo speciale viene chiamato automaticamente quando crei un nuovo oggetto (istanza) della classe.
  # Serve per inizializzare gli attributi dell'oggetto.
  # 'self' è un riferimento all'istanza specifica dell'oggetto che viene creato.
  # Dopo 'self', puoi aggiungere i parametri che vuoi passare quando crei l'oggetto.
  def __init__(self):

      # --- Attributi dell'Istanza ---
      # Questi sono i dati specifici di ogni oggetto creato da questa classe.
      # Si definiscono usando 'self.nome_attributo = valore'
      self.QRNG_type = None
      self.list_of_numbers = list()
      self.stats = None
      self.qc = None
      self.qubits_number = None
      self.pvalues_results = None

  # --- Metodi dell'Istanza ---
  def QCType0(self,n):
    qc = QuantumCircuit(n, n)
    qc.h(range(n))
    qc.measure(range(n), range(n))
    return qc

  def QCType1(self,n):
    qc = QuantumCircuit(n, n)
    qc.x(range(n))
    qc.h(range(n))
    qc.measure(range(n), range(n))
    return qc

  def QCType2(self,n):
    qc = QuantumCircuit(n, n)
    qc.h(range(n))
    qc.measure(range(n), range(n))
    qc.h(range(n))
    qc.measure(range(n), range(n))
    return qc

  def QCType3(self,n):
    qc = QuantumCircuit(n, n)
    qc.x(range(n//2, n))
    qc.h(range(n))
    qc.measure(range(n), range(n))
    return qc

  def chooseCircuit(self, QRNG_type, qubits_number):
      """Method to choose the circuit"""
      self.QRNG_type = QRNG_type
      self.qubits_number = qubits_number
      if QRNG_type == 0:
          self.qc = self.QCType0(qubits_number)
      elif QRNG_type == 1:
          self.qc = self.QCType1(qubits_number)
      elif QRNG_type == 2:
          self.qc = self.QCType2(qubits_number)
      elif QRNG_type == 3:
          self.qc = self.QCType3(qubits_number)

  def runCircuit(self, token, quantum_computer,simulation=True, shots=1024, verbose=True):

      """Generates random numbers via quantum computing

      The random numbers are concatenated in order to produce a large one

      Parameters
      ----------
      token : str, optional
        The token to use for the quantum computer (default is None)
      simulation : bool, optional
        If the AER simulator should be used or a real quantum computer (default is True)
      shots : int, optional
        The number of shots to use in the simulation (default is 1024)
      verbose : bool, optional
        If the histogram should be displayed (default is True)

      Returns
      -------
      bit_lst : list
        The array of bits generated by the quantum circuit, flattened and concatened
      """

      # Creation of the quantum circuit
      qc = self.qc


      if simulation:

        # Use of the AER simulator

        backend = Aer.get_backend('aer_simulator')
        options = {"simulator": {"seed_simulator": 100}}
        simulation_sampler = Sampler(backend, options=options)

        pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
        transpiled_qc = pm.run(qc)

        # Generation of the results and creation of the array
        result = simulation_sampler.run([transpiled_qc], shots=shots).result()[0]
        bitstring = result.data.c.get_bitstrings()
        bit_lst = [int(x) for y in bitstring for x in y]

        if verbose:
          # Display the histogram of the results
          display(plot_histogram(result.data.c.get_counts()))
        return bit_lst

      else:

        # Use of a real quantum computer, by default the least_busy one

        service = QiskitRuntimeService(channel='ibm_quantum', token=token)
        backend = service.backend(f"{quantum_computer}")
        #backend = service.least_busy(operational=True)
        options = {"default_shots": shots}

        pm = generate_preset_pass_manager(optimization_level=1, backend=backend)
        qc = pm.run(qc)

        sampler = Sampler(mode=backend, options=options)
        job = sampler.run([qc])

        # Status of the job
        if verbose:
          print(f">>> Job ID: {job.job_id()}")
          print(f">>> Job Status: {job.status()}")

        while job.status() in ['QUEUED', 'RUNNING']:
            if job.status() == 'QUEUED':
                continue
            elif job.status() == 'RUNNING':
                if verbose:
                  print(f">>> Job Status: {job.status()}")
                break

        # Creation of the array and concatenation of the results
        result = job.result()
        bitstring = result[0].data.c.get_bitstrings()
        bit_lst = [int(x) for y in bitstring for x in y]

        if verbose:
          # Display of the histogram
          display(plot_histogram(result[0].data.c.get_counts()))
        return bit_lst

  def generate_Numbers(self, quantum_computer, num_qrn,token,num_shots,verbose,simulation):
    RNG_output = list()

    # Number of iterations for the test
    for i in range(num_qrn):
      RNG_output.append(self.runCircuit(token=token,quantum_computer=quantum_computer, simulation=simulation, shots=num_shots,verbose = verbose))
    self.list_of_numbers = RNG_output
    return self.list_of_numbers


  def retrieve_from_IBM(self, files):

    from qiskit_ibm_runtime import QiskitRuntimeService
    import logging
    qrn_IBM = list()
    for file in files:
      # Leggere gli ID dal file
      with open(f"/content/{file}", "r") as f:
          current_token = f.readline().strip()
          job_ids = [line.strip() for line in f.readlines()]
      print(f" IBM account: {file}")
      service = QiskitRuntimeService(
          channel='ibm_quantum',
          instance='ibm-q/open/main',
          token=current_token
      )
      # Iterare sugli ID e recuperare i risultati
      for job_id in job_ids:
          try:
              job = service.job(job_id)
              result = job.result()
              idx = 0  # Primo circuito nel job
              bitstring = result[idx].data.c.get_counts()

              # Convertire in lista di bit
              bit_lst = [int(x) for y in bitstring for x in y]
              qrn_IBM.append(bit_lst)
              print(f"Job {job_id} elaborato con successo.")
          except IBMBackendError as e:
            logging.error(f"Errore di backend IBM per il job {job_id}: {e}")
            # ... (eventuale meccanismo di ripristino) ...
            print(f"Errore di backend IBM per il job {job_id}: {e}")
          except Exception as e:
              logging.exception(f"Errore non programmato con il job {job_id}: {e}")
              print(f"Errore non programmato con il job {job_id}: {e}")
    return qrn_IBM

  def create_N_bits_sequences(self, list_of_numbers, sequence_length):
    """
    Creates sequences of a specified length from the list_of_numbers.

    Args:
      list_of_numbers: The list of random numbers.
      sequence_length: The desired length of each sequence.

    Returns:
      A list of sequences with the specified length.
    """

    # Flatten the list of lists into a single list
    flattened_list = [bit for sublist in list_of_numbers for bit in sublist]

    # Check if there are enough bits to create at least one sequence
    if len(flattened_list) < sequence_length:
      print(f"Error: Not enough bits to create a sequence of length {sequence_length}.")
      return []
    print(f"Len flattened_list: {len(flattened_list)}")
    # Calculate the number of sequences that can be created
    num_sequences = len(flattened_list) // sequence_length
    print(f"Number of sequences: {num_sequences}")

    # Create a list of sequences
    sequences = []
    for i in range(num_sequences):
      start_index = i * sequence_length
      end_index = (i + 1) * sequence_length
      sequences.append(flattened_list[start_index:end_index])

    return sequences

  def NIST_tests(self,verbose,list_qrns = None):
    # Tests and results
    if list_qrns == None:
      list_qrns = self.list_of_numbers
    # otherwise i will use the qrns retrieved from IBM composer

    list_results = list()
    for i in range(len(list_qrns)):
      # Tests are made and put in a dictionary
      results = {}
      results["Frequency (Monobit)"] =            frequency(list_qrns[i])
      results["Frequency within Block"] =         block_frequency(list_qrns[i], 10000)
      results["Runs"] =                           runs(list_qrns[i])
      results["Longest Runs in Block"] =          longest_run_of_ones(list_qrns[i])
      results["Matrix Rank"] =                    rank(list_qrns[i])
      results["Discrete Fourier Transform"] =     discrete_fourier_transform(list_qrns[i])
      results["Overlapping Template Matching"] =  overlapping_template_matchings(list_qrns[i], 10)
      results["Maurer's Universal"] =             universal(list_qrns[i])
      results["Linear Complexity"] =              linear_complexity(list_qrns[i], 1000)
      results["Serial"] =                         serial(list_qrns[i], 17)
      results["Approximate Entropy"] =            approximate_entropy(list_qrns[i], 14)
      results["Cumulative Sums (Cusum)"] =        cumulative_sums(list_qrns[i])
      results["Random Excursions"] =              random_excursions(list_qrns[i])
      results["Random Excursions Variant"] =      random_excursions_variant(list_qrns[i])
      list_results.append(results)

    # Creation of the table to display the results nicely
    for i in range(len(list_results)):
      table = []
      for test, p_value in list_results[i].items():
        if isinstance(p_value, (int, float)):  # Assicura che sia un numero
            outcome = "PASS" if p_value > 0.01 else "FAIL"
            table.append([test, round(p_value, 3), outcome])
        elif isinstance(p_value, list):  # Per test che restituiscono liste di p-value
            for j, val in enumerate(p_value):
                if isinstance(val, (int, float)):
                    outcome = "PASS" if val > 0.01 else "FAIL"
                    table.append([f"{test} {j}", round(val, 3), outcome])
                else:
                    table.append([f"{test} {j}", "ERROR", "FAIL"])
        else:
            table.append([test, "ERROR", "FAIL"])
      self.pvalues_results = list_results
      if verbose == True:
        print(tabulate(table, headers=["Test " + str(i), "p-value", "Verdict"]))
        print("")

  def proportion_passed_sequences_test(self, alpha=0.01,save_images = True):
    import numpy as np
    from scipy.stats import norm
    from tabulate import tabulate # Non più necessario se non stampi la tabella
    import matplotlib.pyplot as plt
    import math # Necessario per isnan

    # --- Calcoli Esistenti ---
    # Definizione del livello di significatività e dell'intervallo di confidenza
    if not hasattr(self, 'pvalues_results') or not self.pvalues_results:
        print("Errore: Nessun risultato di p-value trovato ('self.pvalues_results' è vuoto o non esiste).")
        return
    num_sequences = len(self.pvalues_results)
    if num_sequences == 0:
        print("Errore: La lista 'self.pvalues_results' è vuota.")
        return

    expected_proportion = 1 - alpha  # Proporzione attesa di test passati

    # Calcola l'intervallo di confidenza usando il metodo Z-score (norm.ppf)
    # Nota: NIST SP 800-22 usa spesso una regola più semplice: +/- 3 * sqrt(alpha*(1-alpha)/num_sequences)
    # Questo codice usa l'IC statistico standard basato sull'approssimazione normale.
    z_score = norm.ppf(1 - alpha / 2)
    # Aggiungi un controllo per evitare divisione per zero o radice di numero negativo
    if num_sequences > 0 and (expected_proportion * alpha) >= 0:
         confidence_margin = z_score * np.sqrt((expected_proportion * alpha) / num_sequences)
    else:
         confidence_margin = 0 # O gestisci l'errore come preferisci
         print("Attenzione: Impossibile calcolare il margine di confidenza (num_sequences <= 0 o alpha non valido).")

    lower_bound = expected_proportion - confidence_margin
    upper_bound = expected_proportion + confidence_margin

    # Funzione helper per calcolare il tasso di successo gestendo None/NaN
    def calculate_pass_rate(p_values, alpha_level):
        """Calcola la proporzione di sequenze passate per un test specifico."""
        if not p_values: # Gestisce lista vuota per un test
             return np.nan # O 0, o solleva errore
        # Filtra None e NaN prima della conversione e calcolo
        valid_p_values = [p for p in p_values if p is not None and not math.isnan(p)]
        if not valid_p_values: # Se non ci sono p-value validi dopo il filtro
             return np.nan
        p_values_arr = np.array(valid_p_values)
        pass_rate = np.mean(p_values_arr >= alpha_level)
        return pass_rate

    # Aggregare tutti i p-values dai risultati dei test
    aggregated_p_values = {}
    for result in self.pvalues_results:
        # Assicurati che result sia un dizionario
        if not isinstance(result, dict):
            # print(f"Attenzione: Saltato un risultato non dizionario in self.pvalues_results: {result}")
            continue # Salta questo risultato se non è un dizionario
        for test, p_value in result.items():
            if test not in aggregated_p_values:
                aggregated_p_values[test] = []

            # Gestisce p_value None o NaN e liste/valori singoli in modo robusto
            current_p_list = []
            if isinstance(p_value, list):
                # Filtra None/NaN dalla lista
                current_p_list = [p for p in p_value if p is not None and not math.isnan(p)]
            elif p_value is not None and not math.isnan(p_value):
                 # Trasforma il valore singolo in lista
                 current_p_list = [p_value]
            # else: p_value è None o NaN, non fare nulla

            if current_p_list: # Aggiungi solo se ci sono p-value validi
                aggregated_p_values[test].extend(current_p_list)

    # --- Estrai i Dati per il Plotting ---
    test_names_all = list(aggregated_p_values.keys())
    # Calcola solo i tassi di successo numerici
    pass_rates_values_all = [calculate_pass_rate(aggregated_p_values.get(test, []), alpha) for test in test_names_all]

    # Filtra i test per cui non è stato possibile calcolare un tasso (risultato NaN)
    valid_indices = [i for i, rate in enumerate(pass_rates_values_all) if not np.isnan(rate)]
    if not valid_indices:
         print(f"Errore: Nessun tasso di successo valido calcolabile per alpha={alpha}.")
         return # Non possiamo plottare nulla

    test_names = [test_names_all[i] for i in valid_indices]
    pass_rates_values = [pass_rates_values_all[i] for i in valid_indices]
    num_tests = len(test_names)
    test_numbers = np.arange(1, num_tests + 1) # Numeri da 1 a num_tests

    table_data = []
    for i in range(len(test_names)):
        test_name = test_names[i]
        pass_rate = pass_rates_values[i]
        verdict = "PASS" if lower_bound <= pass_rate <= upper_bound else "FAIL"
        table_data.append([test_name, pass_rate, expected_proportion, verdict])
    print(tabulate(table_data, headers=["Test", "Pass Rate", "Verdict"]))
    # --- Codice di Plotting (Adattato) ---
    plt.figure(figsize=(15,10)) # Aumentata leggermente per le etichette ruotate

    # Plotta le proporzioni osservate come punti neri
    plt.plot(test_numbers, pass_rates_values, 'ko', label='Proportion observed') # 'ko' = black circle marker

    # Plotta la linea della proporzione attesa
    plt.axhline(y=expected_proportion, color='k', linestyle='-', linewidth=1, label=f'Expected ({expected_proportion:.2f})')

    # Plotta le linee dell'intervallo di confidenza
    plt.axhline(y=lower_bound, color='k', linestyle='--', linewidth=1, label=f'Interval Conf. [{lower_bound:.6f}, {upper_bound:.6f}]')
    plt.axhline(y=upper_bound, color='k', linestyle='--', linewidth=1)

    # Aggiungi etichette testuali per i limiti (opzionale, come nell'immagine di riferimento)
    # Usa trasformazione assi per posizionamento relativo; sfondo semi-trasparente per leggibilità
    plt.text(0.01, upper_bound, f'{upper_bound:.6f}', transform=plt.gca().get_yaxis_transform(), va='bottom', ha='left', fontsize=9, backgroundcolor=(1,1,1,0.7))
    plt.text(0.01, lower_bound, f'{lower_bound:.6f}', transform=plt.gca().get_yaxis_transform(), va='top', ha='left', fontsize=9, backgroundcolor=(1,1,1,0.7))


    # --- Formattazione del Grafico ---
    plt.title(f'Proportin of passed sequences for Test NIST (m={num_sequences}, alpha={alpha})')
    plt.xlabel('Test NIST')
    plt.ylabel('Proportion passed')

    # Imposta i tick sull'asse X usando i numeri dei test come posizioni e i nomi dei test come etichette
    plt.xticks(ticks=test_numbers, labels=test_names, rotation=45, ha='right') # Ruota le etichette per leggibilità

    # Regola i limiti dell'asse Y per focalizzare sull'intervallo rilevante
    min_observed = min(pass_rates_values) if pass_rates_values else lower_bound
    max_observed = max(pass_rates_values) if pass_rates_values else upper_bound

    # Aggiungi un po' di padding attorno ai limiti e ai dati osservati
    padding = 0.005 # Puoi aggiustare questo valore
    plot_min_y = min(lower_bound, min_observed) - padding
    plot_max_y = max(upper_bound, max_observed) + padding
    # Assicura limiti ragionevoli (proporzione tra 0 e 1)
    plot_min_y = max(0.0, plot_min_y) # Non può essere < 0
    plot_max_y = min(1.0 + padding, plot_max_y) # Leggermente sopra 1.0 se necessario
    plt.ylim(plot_min_y, 1.2)

    plt.grid(axis='y', linestyle=':', linewidth=0.5) # Griglia orizzontale leggera
    plt.legend(loc='best') # Lascia che matplotlib scelga la posizione migliore per la legenda

    plt.tight_layout() # Aggiusta il layout per evitare sovrapposizioni

    if save_images:
        # Crea una cartella per le immagini se non esiste
        import os
        if not os.path.exists("test_images"):
            os.makedirs("test_images")

        # Salva l'immagine nella cartella creata
        plt.savefig(f"test_images/proportion_sequences.png")

    plt.show()

  def uniformity_test(self,alpha = 0.01,save_images = True):
    import scipy.stats as stats
    from scipy.special import gammaincc  # Import the necessary function
    import numpy as np
    import matplotlib.pyplot as plt
    from tabulate import tabulate

    def test_uniformity_p_values(test_name, p_values, save_images, k=10, alpha=alpha):
        """
        Esegue il test di uniformità dei p-value usando il chi-quadrato,
        genera un istogramma dei p-value e restituisce i risultati in formato tabellare.

        Args:
            test_name (str): Nome del test NIST.
            p_values (list): Lista di p-value.
            k (int): Numero di intervalli (default: 10).
            alpha (float): Livello di significatività (default: 0.0001).

        Returns:
            str: Tabella formattata dei risultati del test chi-quadrato.
        """

        intervals = np.linspace(0, 1, k + 1)
        observed_frequencies, _ = np.histogram(p_values, bins=intervals)
        # The expected frequencies should sum to the total number of p-values
        expected_frequency = len(p_values) / k
        expected_frequencies = np.full(k, expected_frequency)

        # Ensure observed frequencies and expected frequencies have the same sum
        # Adjust observed frequencies to match the sum of expected frequencies
        #observed_frequencies = observed_frequencies * np.sum(expected_frequencies) / np.sum(observed_frequencies)


        chi_squared, p_ii = stats.chisquare(observed_frequencies, expected_frequencies)

        # Calculate P-value using igamc (gammaincc):
        p_ii = gammaincc(9/2, chi_squared/2)

        verdict = "FAIL" if p_ii < alpha else "PASS"

        table = [
            ["Test Name", test_name],
            ["Chi-Squared", chi_squared],
            ["p_II", p_ii],
            ["Verdict", verdict]
        ]

        # Genera l'istogramma
        plt.hist(p_values, bins=intervals, edgecolor='black')
        plt.xlabel("p-value")
        plt.ylabel("Frequency ")
        plt.title(f"P-value distribution - {test_name}")
        plt.text(0.95, 0.95, verdict,  # Adjust position as needed
             horizontalalignment='right',
             verticalalignment='top',
             transform=plt.gca().transAxes,  # Use axes coordinates
             fontsize=12,  # Adjust font size as needed
             bbox=dict(facecolor='white', alpha=0.8))  # Add a background box
        if save_images:
        # Crea una cartella per le immagini se non esiste
          import os
          if not os.path.exists("test_images"):
              os.makedirs("test_images")

          # Salva l'immagine nella cartella creata
          plt.savefig(f"test_images/{test_name}_distribution.png")
        plt.show()  # Mostra l'istogramma
        return table # Return the table

    # Aggregare tutti i p-values dai risultati dei test
    aggregated_p_values = {}
    for result in self.pvalues_results:
        for test, p_value in result.items():
            if test not in aggregated_p_values:
                aggregated_p_values[test] = []
            # Se p_value è una lista, la estendiamo, altrimenti lo trasformiamo in lista e lo aggiungiamo
            aggregated_p_values[test].extend(p_value if isinstance(p_value, list) else [p_value])

    # Creazione della tabella con i risultati elaborati
    table = [test_uniformity_p_values(test_name=test,p_values=p_values,save_images = save_images ) for test, p_values in aggregated_p_values.items()]


  def statistical_test(self, alpha,list_qrns = None):
    self.NIST_tests(verbose=True,list_qrns=list_qrns)
    self.proportion_passed_sequences_test(alpha = alpha)
    self.uniformity_test(alpha = alpha)

  def von_neumann_corrector(self, raw_bits_list):
    """
    Applica il correttore di Von Neumann a una lista di bit (interi 0 o 1).

    Questa tecnica riduce il bias di primo ordine prendendo i bit a coppie
    non sovrapposte e generando output solo per le coppie (0, 1) (output 0)
    o (1, 0) (output 1). Le coppie (0, 0) e (1, 1) vengono scartate.

    Args:
        raw_bits_list: Una lista (o vettore) contenente la sequenza binaria
                       grezza come interi (es. [0, 1, 1, 0, ...]).

    Returns:
        Una lista contenente la sequenza di bit post-processata e
        de-biasata come interi. Sarà significativamente più corta dell'input.
        Restituisce una lista vuota se l'input è troppo corto o
        non produce output.
    """
    processed_bits = []  # Lista per accumulare i bit di output (come interi)
    n = len(raw_bits_list)

    # Itera attraverso i bit grezzi prendendo coppie non sovrapposte
    for i in range(0, n - 1, 2):  # Incrementa l'indice di 2
        # Estrae la coppia come tupla di interi
        bit1 = raw_bits_list[i]
        bit2 = raw_bits_list[i + 1]
        pair = (bit1, bit2)

        # Applica le regole di Von Neumann confrontando tuple di interi
        if pair == (0, 1):
            processed_bits.append(0)  # Aggiunge l'intero 0
        elif pair == (1, 0):
            processed_bits.append(1)  # Aggiunge l'intero 1
        # Le coppie (0, 0) e (1, 1) vengono ignorate

    return processed_bits

  def generate_TOTP(self,bit_list):

    # Creation of the base32 chunks from the list of bits
    bit_list = ["".join(str(bit_list[i]) for i in range(j, j + 5)) for j in range(len(bit_list) // 5)]
    #print([int(x, 2) for x in bit_list])

    # Generation of the base32 secret
    characters_list = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ234567")
    secret = "".join(characters_list[int(bit, 2)] for bit in bit_list)
    #print(secret)
    totp = pyotp.TOTP(secret)
    # Generation of the OTPs
    return totp

  def generate_HOTP(self,bit_list):

    # Creation of the base32 chunks from the list of bits
    bit_list = ["".join(str(bit_list[i]) for i in range(j, j + 5)) for j in range(len(bit_list) // 5)]
    #print([int(x, 2) for x in bit_list])

    # Generation of the base32 secret
    characters_list = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ234567")
    secret = "".join(characters_list[int(bit, 2)] for bit in bit_list)
    #print(secret)
    hotp = pyotp.HOTP(secret)
    # Generation of the OTPs
    return hotp


  # Puoi aggiungere quanti metodi vuoi per definire il comportamento degli oggetti
  def __str__(self):
      """
      Metodo speciale che definisce come l'oggetto deve essere rappresentato
      come stringa (es. quando usi print()).
      """
      return f"Oggetto MiaClasse(attributo1='{self.attributo1}', attributo2='{self.attributo2}')"

# def save(mia_lista_di_liste):
#   import json
#   try:
#     # Apri il file in modalità scrittura ('w' - write)
#     with open("qrns.json", 'w', encoding='utf-8') as f:
#         # Usa json.dump() per scrivere la lista nel file
#         # indent=4 rende il file JSON più leggibile (opzionale)
#         json.dump(mia_lista_di_liste, f, indent=4)
#     print(f"Lista salvata con successo nel file")

#   except Exception as e:
#     print(f"Errore durante il salvataggio in JSON: {e}")
#     def load(nome_file_json):
#   import json
#   lista_caricata_json = None # Inizializza la variabile
#   try:
#       # Apri lo stesso file in modalità lettura ('r' - read)
#       with open(nome_file_json, 'r', encoding='utf-8') as f:
#           # Usa json.load() per leggere i dati dal file e ricostruire la lista
#           lista_caricata_json = json.load(f)
#       print(f"\nLista caricata con successo da {nome_file_json}:")
#       return lista_caricata_json
#       # Verifica che sia uguale all'originale
#       # print(lista_caricata_json == mia_lista_di_liste)

#   except FileNotFoundError:
#       print(f"\nErrore: Il file {nome_file_json} non è stato trovato.")
#   except json.JSONDecodeError:
#       print(f"\nErrore: Il file {nome_file_json} non contiene dati JSON validi.")
#   except Exception as e:
#       print(f"\nErrore durante il caricamento da JSON: {e}")

"""# Examples of functions

We create the instance of the quantum random number, we choose the type of circuit that we want to use to run our circuit(we can choose between 0,1,2,3) and then we use the function generate_Numbers to produce a given amount of numbers
"""

g = QRNG()
g.chooseCircuit(QRNG_type=2, qubits_number=16)
g.generate_Numbers(num_qrn = 2, token = None,quantum_computer = "ibm_sheerbroke", num_shots = 1024, verbose = True, simulation = True)

"""In this code snippet we create the quantum random number directly from an account, specifying the token"""

# 65 mila shots to have a 1 milion bit number
# "447ab388994f0e83d45c52c41eb003beb31c6932a2e941e60b3b3a708a0995449d76517def2e1d141287186156dbfb2bef29095442da9d1e62ed9e329ff843e3"
g = QRNG()
g.chooseCircuit(QRNG_type=3, qubits_number=16)
M_number = g.generate_Numbers(num_qrn = 50, token ="" ,quantum_computer = "ibm_sheerbroke", num_shots = 65000, verbose = False, simulation = False)

"""In this code snippet, we use the function retrieve_from_IBM to retrieve the jobs from the different account(since we have only 10 minutes available for each one) and the function will collapse the results in only one output.
The txt file should formatted to have the token in the first row and in the following all the job_ids
"""

lista_job = [
    "job_alex_1.txt",
    "job_mirko_2cav.txt",
    "job_alex_2.txt",
    "job_mirko_3hotmail.txt",
    "job_alex_3.txt",
    "job_vito1_pallavolo.txt",
    "job_gianlu1.txt",
    "job_vito2_s333996.txt",
    "job_gianlu2gianluca.schiano@yahoo.txt",
    "job_vito_3vitocucinelli05.txt",
    "job_gianlu3schianog399.txt",
    "job_vito_4vitov2.txt",
     "job_mirko_1.txt"

]
qrns_from_IBM = g.retrieve_from_IBM(files = lista_job)

"""In some cases(like with type 2 circuit) could be usefull to produce smaller string of bit, and with these produce a bigger number by concatenation.
The concatenation is an operation that can be done without problem, because if the quantum random number generator is biased,will amplify the effect of each sequence. So it's the same as producing a bigger list of bit
"""

M_numbers = g.create_N_bits_sequences(qrns_from_IBM,1000000)

"""We choose the parameter alpha to use to run statistical test. The parameter indicates the number of numbers that will fail the test(in this case only 1% of the sample size)"""

g.statistical_test(alpha = 0.01,list_qrns=M_numbers)

"""Maximum number of shots



"""

from qiskit_ibm_provider import IBMProvider
provider = IBMProvider(token="3338c3c09a32e05b237b4f20d01c8ed61b80d85849cdb0b3181ef0add46021ec93104e0a69852890e1a9999bec61ba088b7d2dcd86310d8f5755bdcb539f4ccf") # Carica le tue credenziali
backend = provider.get_backend('ibm_sheerbroke') # Sostituisci con il backend desiderato
max_shots_limit = backend.configuration().max_shots
print(f"Il limite massimo di shots per {backend.name} è: {max_shots_limit}")

"""Generation of OTPs"""

bit_list = qrns_from_IBM[0] # can be also chosen randomly from my numbers
totp = g.generate_TOTP(bit_list)
hotp = g.generate_HOTP(bit_list)

# Changes every 30s
# for i in range(10):
#   print(totp.now())
#   sleep(10)

#print(hotp.at(1))

"""# Statistical analisys

This statistical analisys is conducted on type 3 circuit runned on sherbrooke
"""

g = QRNG()
g.chooseCircuit(QRNG_type=3, qubits_number=16)

# lista_job = [
#       "job_vito5.txt"]

lista_job = [
     "job_vito5.txt",
      "job_vito6.txt",
      "job_vito7.txt",
     "job_vito8.txt",
     "job_vito9.txt"
]
qrns_from_IBM = g.retrieve_from_IBM(files = lista_job)

g.statistical_test(alpha = 0.01,list_qrns=qrns_from_IBM)

"""# Von Neumann post processing

"""

prova = qrns_from_IBM
new_prova = []
for i in range(len(prova)):
  new_prova.append(g.von_neumann_corrector(prova[i]))

"""Let's how much is reduced the string of bits after the post processing"""

print(len(new_prova[0]))

g.statistical_test(alpha = 0.01,list_qrns=new_prova)