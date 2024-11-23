import csv
import random
import copy
from tabulate import tabulate

DAYS = ['Понеділок', 'Вівторок', 'Середа', 'Четвер', "П'ятниця"]
SLOTS_PER_DAY = 4
MAX_CLASSES_PER_WEEK = 20


def load_csv(filename):
    with open(filename, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        return [row for row in reader]


groups = load_csv('data/groups.csv')
teachers = load_csv('data/teachers.csv')
courses = load_csv('data/courses.csv')
rooms = load_csv('data/rooms.csv')


def generate_schedule():
    schedule = []

    for group in groups:
        group_courses = [c for c in courses if group['name'] in c['groups'].split(',')]
        for course in group_courses:
            for _ in range(int(course['hours'])):
                valid = False
                while not valid:
                    day = random.choice(DAYS)
                    slot = random.randint(1, SLOTS_PER_DAY)
                    room = random.choice(rooms)
                    teacher = random.choice(
                        [t for t in teachers if course['name'] in t['courses'].split(',')]
                    )
                    entry = {
                        'day': day,
                        'slot': slot,
                        'room': room['name'],
                        'group': group['name'],
                        'course': course['name'],
                        'teacher': teacher['name']
                    }
                    if check_constraints(schedule + [entry]):
                        valid = True
                        schedule.append(entry)
    return schedule


def check_constraints(schedule):
    penalties = 0
    time_table = {}

    for entry in schedule:
        key = (entry['day'], entry['slot'])
        if key not in time_table:
            time_table[key] = {'rooms': set(), 'teachers': set(), 'groups': set()}

        if entry['room'] in time_table[key]['rooms']:
            penalties += 1
        if entry['teacher'] in time_table[key]['teachers']:
            penalties += 1
        if entry['group'] in time_table[key]['groups']:
            penalties += 1

        time_table[key]['rooms'].add(entry['room'])
        time_table[key]['teachers'].add(entry['teacher'])
        time_table[key]['groups'].add(entry['group'])

    return penalties == 0


def fitness(schedule):
    penalties = 0
    group_slots = {group['name']: [] for group in groups}

    for entry in schedule:
        group_slots[entry['group']].append((entry['day'], entry['slot']))

        group_students = next(filter(lambda x: x['name'] == entry['group'], groups))['num_students']
        room_capacity = next(filter(lambda x: x['name'] == entry['room'], rooms))['capacity']
        if group_students > room_capacity:
            penalties += 1

        teacher_courses = next(filter(lambda x: x['name'] == entry['teacher'], teachers))['courses'].split(',')
        if entry['course'] not in teacher_courses:
            penalties += 1

    for entry in schedule:
        group_slots[entry['group']].append((entry['day'], entry['slot']))

    for slots in group_slots.values():
        days = set(slot[0] for slot in slots)
        for day in days:
            daily_slots = sorted(slot[1] for slot in slots if slot[0] == day)
            for i in range(len(daily_slots) - 1):
                if daily_slots[i + 1] - daily_slots[i] > 1:
                    penalties += 1

    return 1 / (penalties + 1)
    # return -penalties


def get_tournament_selection(population, selection_size):
    return sorted(random.sample(population, selection_size), key=fitness, reverse=True)[0]


def mutate(schedule, mutation_rate):
    for entry in random.sample(schedule, int(len(schedule) * mutation_rate)):
        valid = False

        while not valid:
            old_entry = copy.deepcopy(entry)

            entry['day'] = random.choice(DAYS)
            entry['slot'] = random.randint(1, SLOTS_PER_DAY)
            entry['room'] = random.choice(rooms)['name']
            entry['teacher'] = random.choice([t for t in teachers if entry['course'] in t['courses'].split(',')])['name']

            if check_constraints(schedule):
                valid = True
            else:
                entry['day'] = old_entry['day']
                entry['slot'] = old_entry['slot']
                entry['room'] = old_entry['room']
                entry['teacher'] = old_entry['teacher']
    return schedule


def genetic_algorithm(population_size=20, elite_size=2, tournament_selection_size=10, mutation_rate=0.1):
    population = sorted([generate_schedule() for _ in range(population_size)], key=fitness, reverse=True)
    generation = 1
    data = []
    while fitness(population[0]) != 1:
        assert all([check_constraints(s) for s in population])

        for schedule in population:
            mutate(schedule, mutation_rate)
        population.sort(key=fitness, reverse=True)

        next_population = []
        for _ in range(len(population)):
            next_population.append(copy.deepcopy(population[0]))

        # next_population = population[:elite_size]
        # for _ in range(population_size - elite_size):
        #     tournament = random.sample(population, tournament_selection_size)
        #     tournament.sort(key=fitness, reverse=True)
        #     next_population.append(copy.deepcopy(tournament[0]))

        population = next_population
        population.sort(key=fitness, reverse=True)
        print(f'Generation {generation}: Best fitness = {fitness(population[0])}')
        data.append([generation, *list(map(lambda x: fitness(x), population[:3]))])
        generation += 1
    print(tabulate(data, ['Generation', 'Fitness 1', 'Fitness 2', 'Fitness 3']))
    return population[0]


def save_schedule(schedule, filename='output/schedule.csv'):
    keys = schedule[0].keys()
    with open(filename, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()
        writer.writerows(schedule)


if __name__ == '__main__':
    best_schedule = genetic_algorithm()
    save_schedule(best_schedule)
