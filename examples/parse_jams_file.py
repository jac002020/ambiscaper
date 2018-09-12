# Open the soundscape `soundscape_for_test` generated by `generate_test_files.py` and extract the information



from ambiscaper import *
import os
import jams

# Add Ambiscaper namespaces
jams.schema.add_namespace(os.path.abspath('../ambiscaper/namespaces/ambiscaper_sound_event.json'))
jams.schema.add_namespace(os.path.abspath('../ambiscaper/namespaces/ambiscaper_sofa_reverb.json'))

# Set target soundscape path
soundscape_path = os.path.abspath('../tests/data/soundscape_for_test')
soundscape_jams_file_name = os.path.join(soundscape_path,'soundscape_for_test.jams')

# Load jams file
jam = jams.load(soundscape_jams_file_name, validate=False, strict=False)

# Let's find the `ambiscaper_sound_event` AnnotationArray.
# The `search` method returns all annotations that matches the namespace query.
# In our case, there should be only one annotation.
event_annotation_array = jam.search(namespace='ambiscaper_sound_event')
event_annotation = event_annotation_array[0]

# `event_annotation` is an instance of the Annotation class
# We can check the annotation contents with a print call
print(event_annotation)
# The Annotation class provides some handful methods to manage the data,
# for example slice(), trim(), etc.
# Please refer to the Jams documentation for more info.


# Annotations provide some convenience fields for holding the data.
# These fields can be accessed as variables of the instance.
# In the case of the `ambiscaper_sound_event` namespace, this is the description:
# - namespace: the string name of the namespace
# - sandbox: an instance of Sandbox, holding the event specs
# - time
# - duration
# - annotation_metadata
# - data: a JamsFrame instance with the actual instanciated spec

# The most interesting field for now is `data`, which contains the
# groundtruth values of the soundscape.
# It is an instance of `JamsFrame`
event_data = event_annotation.data
# Printing the data will give us a nice list with the different events,
# ordered by appearance time
print(event_data)
# And the total number of events (foreground and background) will be given by len()
print('Number of different events:',len(event_data))
# It is also possible to get the event intervals (instead of time, duration)
print(event_data.to_interval_values()[0])

# We can iterate over the events and get the values:
for event_idx, data in event_data.iterrows():
    print('Event idx',event_idx)
    print('data',data)

# Each `JamsFrame` contains four fields:
# - Duration
# - Confidence
# - Time
# - Value
# The most relevant is the `Value` field, which contains the instanciated values.

# Let's say we want to retrieve the field `event_id` from each event:
print([data.value['event_id'] for event_idx, data in event_data.iterrows()])


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# Replicate an experiment through the annotation!

# As we stated before, the Sandbox field contains the event specification (before instanciation).
# Therefore, it is possible to retrieve all values from the database generation.
# Not only the actual instanciated values (`event_annotation.data`), but _also_ the event spec data,
# i.e., the distribution tuples we gave to the system.
# In that way, it is possible to replicate a database, or an experimental setup, only by exchanging
# the event specifications, with no need for exchanging the actual audio databases.

# sandbox is a `Sandbox` instance with only one field (`ambiscaper`)
# Beneath `ambiscaper`, we have a dictionary with all the instanciation values
event_sandbox = event_annotation.sandbox['ambiscaper']
for key, value in event_sandbox.iteritems():
    print('Key:',key, 'Value:', value)
# We can retrieve in that way, for example, the path for the foreground samples:
print('Foreground path:', event_sandbox['fg_path'])

# It is interesting to check more in detail the `bg/fg_spec`.
fg_spec = event_sandbox['fg_spec']
bg_spec = event_sandbox['bg_spec'][0] # only one background
print(type(fg_spec))
# `fg_spec` is a list containing all the given event spec definitions.
# It has a first dimension length of size `event_sandbox['n_events']`, which is the number of fg events
assert len(fg_spec) == event_sandbox['n_events']
# In turn, each individual fg event is a list, containing distribution tuple values.
# The order of the list elements correspond with the `ambiscaper.EventSpec` definition.
# (Refer to it at the top of ambiscaper/core.py)

# Therefore, we can already create an ambiscaper instance,
# and add the distribution tuples from the data from fg_spec

ambiscaper = AmbiScaper(duration = event_sandbox['duration'],
                        ambisonics_order = event_sandbox['ambisonics_order'],
                        fg_path = event_sandbox['fg_path'],
                        bg_path = event_sandbox['bg_path'])
ambiscaper.ref_db = event_sandbox['ref_db']


def list_to_tuple(list):
    """
    Just ensure that None lists yield None
    """
    if list is None:
        return None
    else:
        return tuple(list)

# Add background
source_file = list_to_tuple(bg_spec[0])
source_time = list_to_tuple(bg_spec[2])
ambiscaper.add_background(
    source_file=source_file,
    source_time=source_time)

# Add foreground
for spec in fg_spec:
    source_file     = list_to_tuple(spec[0])
    # event_id is automatically assigned
    source_time     = list_to_tuple(spec[2])
    event_time      = list_to_tuple(spec[3])
    event_duration  = list_to_tuple(spec[4])
    event_azimuth   = list_to_tuple(spec[5])
    event_elevation = list_to_tuple(spec[6])
    event_spread    = list_to_tuple(spec[7])
    snr             = list_to_tuple(spec[8])
    # role is automatically assigned
    pitch_shift     = list_to_tuple(spec[10])
    time_stretch    = list_to_tuple(spec[11])

    ambiscaper.add_event(
        source_file=source_file,
        source_time=source_time,
        event_time=event_time,
        event_duration=event_duration,
        event_azimuth=event_azimuth,
        event_elevation=event_elevation,
        event_spread=event_spread,
        snr=snr,
        pitch_shift=pitch_shift,
        time_stretch=time_stretch)

outfolder = os.path.abspath('../tests/data/soundscape_for_test_2')
ambiscaper.generate(destination_path=outfolder,
                    generate_txt=True,
                    allow_repeated_source=event_sandbox['allow_repeated_source'])

# The generated soundscape should be equal to the original one!!
# (at least in the event specs, if statistical distributions are involved)