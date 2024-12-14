
import ajiaco as ajc


prj = ajc.Application(
    filename=__file__,
    secret="xcsosslbRaiSUBJUO5Dn42F4Ym4dXETrnxfJjd+YJS4=",
    verbose=True)


prj.set_experiment_sessions_defaults(
    doc="",
    currency_per_point=0.1,
    participation_fee=1.0)


import ipdb; ipdb.set_trace()

# =============================================================================
# SESSIONS
# =============================================================================

# import mpennies

# prj.experiment(mpennies.game)
# prj.experiment(mpennies.game, name="mpennies2")


# =============================================================================
# MAIN
# =============================================================================

# if __name__ == "__main__":
#     prj.run_from_command_line()
