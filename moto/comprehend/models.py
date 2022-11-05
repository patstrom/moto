"""ComprehendBackend class with methods for supported APIs."""

from moto.core import BaseBackend, BaseModel
from moto.core.utils import BackendDict
from moto.utilities.tagging_service import TaggingService
from .exceptions import ResourceNotFound
from typing import Any, Dict, List, Iterable


class EntityRecognizer(BaseModel):
    def __init__(
        self,
        region_name: str,
        account_id: str,
        language_code: str,
        input_data_config: Dict[str, Any],
        data_access_role_arn: str,
        version_name: str,
        recognizer_name: str,
        volume_kms_key_id: str,
        vpc_config: Dict[str, List[str]],
        model_kms_key_id: str,
        model_policy: str,
    ):
        self.name = recognizer_name
        self.arn = f"arn:aws:comprehend:{region_name}:{account_id}:entity-recognizer/{recognizer_name}"
        if version_name:
            self.arn += f"/version/{version_name}"
        self.language_code = language_code
        self.input_data_config = input_data_config
        self.data_access_role_arn = data_access_role_arn
        self.version_name = version_name
        self.volume_kms_key_id = volume_kms_key_id
        self.vpc_config = vpc_config
        self.model_kms_key_id = model_kms_key_id
        self.model_policy = model_policy
        self.status = "TRAINED"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "EntityRecognizerArn": self.arn,
            "LanguageCode": self.language_code,
            "Status": self.status,
            "InputDataConfig": self.input_data_config,
            "DataAccessRoleArn": self.data_access_role_arn,
            "VersionName": self.version_name,
            "VolumeKmsKeyId": self.volume_kms_key_id,
            "VpcConfig": self.vpc_config,
            "ModelKmsKeyId": self.model_kms_key_id,
            "ModelPolicy": self.model_policy,
        }


class ComprehendBackend(BaseBackend):
    """Implementation of Comprehend APIs."""

    def __init__(self, region_name: str, account_id: str):
        super().__init__(region_name, account_id)
        self.recognizers: Dict[str, EntityRecognizer] = dict()
        self.tagger = TaggingService()

    def list_entity_recognizers(
        self, _filter: Dict[str, Any]
    ) -> Iterable[EntityRecognizer]:
        """
        Pagination is not yet implemented.
        The following filters are not yet implemented: Status, SubmitTimeBefore, SubmitTimeAfter
        """
        if "RecognizerName" in _filter:
            return [
                entity
                for entity in self.recognizers.values()
                if entity.name == _filter["RecognizerName"]
            ]
        return self.recognizers.values()

    def create_entity_recognizer(
        self,
        recognizer_name: str,
        version_name: str,
        data_access_role_arn: str,
        tags: List[Dict[str, str]],
        input_data_config: Dict[str, Any],
        language_code: str,
        volume_kms_key_id: str,
        vpc_config: Dict[str, List[str]],
        model_kms_key_id: str,
        model_policy: str,
    ) -> str:
        """
        The ClientRequestToken-parameter is not yet implemented
        """
        recognizer = EntityRecognizer(
            region_name=self.region_name,
            account_id=self.account_id,
            language_code=language_code,
            input_data_config=input_data_config,
            data_access_role_arn=data_access_role_arn,
            version_name=version_name,
            recognizer_name=recognizer_name,
            volume_kms_key_id=volume_kms_key_id,
            vpc_config=vpc_config,
            model_kms_key_id=model_kms_key_id,
            model_policy=model_policy,
        )
        self.recognizers[recognizer.arn] = recognizer
        self.tagger.tag_resource(recognizer.arn, tags)
        return recognizer.arn

    def describe_entity_recognizer(
        self, entity_recognizer_arn: str
    ) -> EntityRecognizer:
        if entity_recognizer_arn not in self.recognizers:
            raise ResourceNotFound
        return self.recognizers[entity_recognizer_arn]

    def stop_training_entity_recognizer(self, entity_recognizer_arn: str) -> None:
        recognizer = self.describe_entity_recognizer(entity_recognizer_arn)
        if recognizer.status == "TRAINING":
            recognizer.status = "STOP_REQUESTED"

    def list_tags_for_resource(self, resource_arn: str) -> List[Dict[str, str]]:
        return self.tagger.list_tags_for_resource(resource_arn)["Tags"]

    def delete_entity_recognizer(self, entity_recognizer_arn: str) -> None:
        self.recognizers.pop(entity_recognizer_arn, None)

    def tag_resource(self, resource_arn: str, tags: List[Dict[str, str]]) -> None:
        self.tagger.tag_resource(resource_arn, tags)

    def untag_resource(self, resource_arn: str, tag_keys: List[str]) -> None:
        self.tagger.untag_resource_using_names(resource_arn, tag_keys)


comprehend_backends = BackendDict(ComprehendBackend, "comprehend")