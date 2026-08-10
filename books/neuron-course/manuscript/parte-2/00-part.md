# Part II — Plain PHP and Composer

No framework. Composer, a CLI script, and the library.

This is the longest part of the book and the one that teaches the most, because there is nowhere for anything to hide. Every object is constructed in front of you, every call is explicit, and when something goes wrong there is no service container to blame.

You will start with a project skeleton and a first agent, then work through the pieces that turn a model call into a system: the message model and the several kinds of memory a conversation needs; tools in real depth, which is where most of the practical difficulty of agentic software lives; structured output that is typed, validated, and retried when the model gets it wrong; streaming and the chunk objects it produces; images and documents; MCP, for connecting to tool servers you did not write; and finally observability and evaluation, so you can find out what your agent actually did and whether it is getting worse.

Every lab in this part runs free and offline on Ollama.

If you came for Laravel, resist the urge to skip ahead. Part V integrates these ideas; it does not teach them.
