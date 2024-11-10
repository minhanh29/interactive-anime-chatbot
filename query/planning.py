# import json
from database import AttributeDao
from .relation import RelationExtractionEngine
from .entity import EntityEngine
from .semantic_search import SemanticSearch


class PlanningEngine:
    def __init__(self):
        self.entity_engine = EntityEngine()
        self.relation_engine = RelationExtractionEngine()

    def query(self, bot_name, prev_context, history, question, speaker, response_queue, verbose=0):
        attribute_list = AttributeDao.get_attribute_list()
        attribute_list.append("none")

        # extract relevant entities
        refined_question, context, need_attribute_dimesion = self.entity_engine.query(
            bot_name=bot_name,
            prev_context=prev_context,
            history=history,
            speaker=speaker,
            question=question,
            attribute_list=attribute_list,
            verbose=verbose
        )

        relevances, importances = SemanticSearch.query(refined_question, k=10)

        context_str = "\n".join(context)
        if prev_context != "":
            context_str = prev_context + "\n" + context_str

        # find relevant relations with entity context
        if need_attribute_dimesion:
            relation_context = self.relation_engine.query(
                current_context=context_str,
                history=history,
                speaker=speaker,
                question=question,
                attribute_list=attribute_list,
                verbose=verbose)
            context.extend(relation_context)

        context = list(set(context))
        return context, relevances, importances
