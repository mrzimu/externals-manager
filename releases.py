from packages import boss_externals, examples

releases = {}

# Add releases from boss_externals
releases.update(examples.releases)
releases.update(boss_externals.releases)