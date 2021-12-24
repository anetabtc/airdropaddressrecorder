from discord.ext import commands
from discord.user import User
from discord.guild import Guild, Member, Role
from dislash import slash_commands
from dislash.interactions import *
import os
import psycopg2
import requests

client = commands.Bot(command_prefix="!")
slash = slash_commands.SlashClient(client)

@slash.command(name="register",description="Register your address for the airdrop.",options=[Option("address","Your ergo wallet address",OptionType.STRING,required=True)])
async def register(interaction: SlashInteraction, address: str):
    r = requests.get(f'{os.environ.get("ERGO_NODE")}/utils/address/{address}')
    res = r.json()
    if res['isValid']:
        guild: Guild = interaction.guild
        member: Member = interaction.author
        user: User = interaction.author
        with psycopg2.connect(host=os.environ.get("POSTGRES_HOST"),port=os.environ.get("POSTGRES_PORT"),database=os.environ.get('POSTGRES_DB'),user=os.environ.get('POSTGRES_USER'),password=os.environ.get('POSTGRES_PASSWORD')) as conn:
            with conn.cursor() as cur:
                cur.execute("""INSERT INTO discord_wallets 
                (guild_id,user_id,user_name,guild_join_date,wallet_address) 
                VALUES 
                (%s,%s,%s,%s,%s)
                ON CONFLICT ON CONSTRAINT "discord_wallets_GUILD_ID_USER_ID"
                DO UPDATE SET
                (user_name, wallet_address, wallet_update_ts)
                = (EXCLUDED.user_name, EXCLUDED.wallet_address, CURRENT_TIMESTAMP)""",(guild.id,user.id,member.display_name,member.joined_at,address))
                conn.commit()
                cur.execute("""
                SELECT count(*) from discord_wallets
                where wallet_registration_ts <= (select wallet_registration_ts from discord_wallets where user_id = '%s' and guild_id = '%s')
                """,(user.id,guild.id))
                count = cur.fetchone()[0]
                if count <= 1000:
                    for r in guild.roles:
                        role: Role = r
                        if role.name == "XMas 21":
                            await member.add_roles(role)
                await interaction.reply(f"Successfully registered your Ergo Wallet address. You were person number {count} to do so.")
    else:
        await interaction.reply("Invalid Ergo wallet address")

client.run(os.environ.get("DISCORD_KEY"))